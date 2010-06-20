import re

from django.dispatch import Signal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import memoize
from django.template.defaultfilters import slugify
from django.utils.importlib import import_module

from .models import Route
from .models import Request

pre_handle = Signal(providing_args=["error", "result"])
post_handle = Signal(providing_args=["error"])

_cache = {}

def _compile_routes(table):
    routes = []
    for entry in table:
        try:
            pattern, handler = entry
        except: # pragma: NOCOVER
            raise ImproperlyConfigured(
                "Bad routing table entry: %s." % repr(entry))

        if not callable(handler):
            try:
                module_name, symbol_name = handler.rsplit('.', 1)
            except: # pragma: NOCOVER
                raise ImproperlyConfigured(
                    "Must be on the form <module_path>.<symbol_name> (got: %s)." % \
                    handler)

            module = import_module(module_name)
            handler = getattr(module, symbol_name)

        regex = re.compile(pattern)
        routes.append((regex, handler))

    return routes

compile_routes = memoize(_compile_routes, _cache, 1)

def split(remaining, table=None):
    """Match text with routing table.

    Text is compared to the routing table and matched in
    sequence. This table is either provided directly in the optional
    ``table`` argument, or looked up under the ``ROUTES`` key in the
    global Django settings.
    """

    if table is None:
        try:
            table = settings.ROUTES
        except AttributeError, exc:
            raise ImproperlyConfigured("No such setting: %s" % str(exc))

    table = tuple(table)
    routes = compile_routes(table)
    excluded = set()

    while True:
        text = remaining.strip()

        for regex, handler in routes:
            if handler in excluded:
                continue

            match = regex.search(text)

            if match is None:
                continue

            yield match, handler
            remaining = text[match.end():]

            # if the match is trivial, we exclude this handler from
            # further processing (prevents infinite recursion and
            # allows trivial matches that use e.g. positive/negative
            # look-ahead to invoke a filter, transform or similar)
            if remaining == text:
                excluded.add(handler)

            break
        else:
            break

        # stop when there's no more text to parse
        if not remaining:
            break

def route(message, table=None):
    """Route message into zero or more requests."""

    for match, handler in split(message.text, table):
        try:
            name = handler.__name__
            route = Route.objects.get(slug=slugify(name))
        except Route.DoesNotExist:
            route = None

        request = Request(message=message, text=match.group(), route=route)
        request.save()

        pre_handle.send(sender=request, handler=handler)
        error = None

        try:
            try:
                response = handler(request, **match.groupdict())
                if not isinstance(response, basestring) and callable(response):
                    response = response()
            except FormatError, error:
                request.erroneous = True
                request.save()
                response = error.text
            except Exception, error:
                raise
            if response is not None:
                text = unicode(response)
                request.respond(message.connection, text)
            if error is not None:
                break
        finally:
            post_handle.send(sender=request, error=error)

class FormatError(Exception):
    """Raised inside a parser to indicate a formatting error. The
    provided ``text`` will be used as the message reply.
    """

    def __init__(self, text):
        self.text = text

class Form(object):
    """Class-based routing."""

    def __init__(self, request=None, **matchdict):
        self.request = request
        self.matchdict = matchdict

    def __call__(self):
        result = self.parse(**self.matchdict) or {}
        return self.handle(**result)

    def parse(self, **kwargs):
        pass

    def handle(self):
        pass

    @property
    def user(self):
        """Return the user object if applicable, or ``None``."""

        return self.request.message.user
