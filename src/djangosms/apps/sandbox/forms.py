from urllib import urlencode
from urllib2 import Request
from urllib2 import urlopen

from picoparse import optional
from picoparse import partial

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from djangosms.core import pico
from djangosms.core.router import Form
from djangosms.core.router import FormatError
from djangosms.core.router import StopError

from .models import Policy

class Forward(Form):
    """Forwards message for users that are not in the sandbox.

    To use this form, the ``SANDBOX_FORWARD_URL`` must be set to an
    HTTP-service that accepts requests on the interface defined by the
    :class:`HTTP <djangosms.core.transports.HTTP>` transport.
    """

    timeout = 3.0

    def parse(self, **kwargs):
        return kwargs

    def handle(self, text=None):
        try:
            policy = Policy.objects.get(user=self.user)
        except Policy.DoesNotExist:
            return

        if policy.enabled:
            return

        try:
            url = settings.SANDBOX_FORWARD_URL
        except AttributeError, error:
            raise ImproperlyConfigured(error)

        self.request.text = text
        self.request.save()

        query = {
            'from': self.request.message.connection.ident,
            'text': self.request.text,
            }

        if '?' not in url:
            url += "?"

        request = Request(
            url+'&'+urlencode(query)
            )

        if not self.fetch(request, timeout=self.timeout):
            raise FormatError(
                "Unexpected system error while processing your message: %s" % \
                request.text)

        # if the operation was succesful, we suppress further
        # processing (without any reply argument).
        raise StopError()

    def fetch(self, request, **kwargs): # pragma: NOCOVER
        response = urlopen(request, **kwargs)
        return response.getcode() // 100 == 2

class Sandbox(Form):
    """Enables or disables sandbox for a registered user.

    Arguments:

    * ``\"on\"``, ``\"1\"``, ``\"yes\"``, ``\"y\"`` enables;
    * ``\"off\"``, ``\"0\"``, ``\"no\"``, ``\"n\"`` disables.

    If no argument is given, the current state is returned.
    """

    @pico.wrap('text')
    def parse(self):
        if optional(partial(pico.one_of_strings, 'on', 'yes', 'y', '1'), False):
            return {'enabled': True}
        if optional(partial(pico.one_of_strings, 'off', 'no', 'n', '0'), False):
            return {'enabled': False}

    def handle(self, **defaults):
        try:
            policy = Policy.objects.get(user=self.user)
        except Policy.DoesNotExist:
            policy, created = Policy.objects.get_or_create(
                user=self.user, defaults=defaults)
        else:
            enabled = defaults.get('enabled')
            if enabled is not None:
                policy.enabled = enabled
                policy.save()

        if policy.enabled:
            return u"Sandbox enabled."

        return u"Sandbox disabled."
