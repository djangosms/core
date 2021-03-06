import re

from django.dispatch import Signal
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.utils.functional import memoize
from django.utils.importlib import import_module

from .models import Route
from .models import Request

pre_handle = Signal(providing_args=["error", "result"])
post_handle = Signal(providing_args=["error"])

_cache = {}

_camelcase_to_underscore = lambda str: re.sub(
    '(((?<=[a-z])[A-Z])|([A-Z](?![A-Z]|$)))', '_\\1', str).lower().strip('_')

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

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except Exception, exc:
            raise ImproperlyConfigured(
                "Invalid regular expression '%s': %s." % (
                    pattern, exc))

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
            slug = _camelcase_to_underscore(handler.__name__)
            route = Route.objects.get(slug=slug)
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
            except StopError, error:
                # this does not mean the message was erroneous; we
                # just extract the (optional) response
                response = error.text
            except Exception, error:
                # catch and re-raise to allow the ``post_handle``
                # signal to receive the exception instance
                raise
            if response is not None:
                text = unicode(response)
                request.respond(message.connection, text)
            if error is not None:
                break
        finally:
            post_handle.send(sender=request, error=error)

class StopError(Exception):
    """Raised from within a handler to indicate that no further
    processing should happen. The provided ``text`` will be used as
    the message reply (optional).
    """

    def __init__(self, text=None):
        self.text = text

    def __str__(self):
        return self.text

class FormatError(Exception):
    """Raised from within a handler to indicate a formatting
    error. The provided ``text`` will be used as the message reply
    (optional).
    """

    def __init__(self, text=None):
        self.text = text

    def __str__(self):
        return self.text

class Form(object):
    """Class-based routing."""

    def __init__(self, request=None, **matchdict):
        self.request = request
        self.matchdict = matchdict

    def __call__(self):
        result = self.parse(**self.matchdict) or {}
        if result is None:
            raise FormatError()
        return self.handle(**result)

    def parse(self, **kwargs):
        pass

    def handle(self):
        pass

    @property
    def user(self):
        """Return the user object if applicable, or ``None``."""

        return self.request.message.user
