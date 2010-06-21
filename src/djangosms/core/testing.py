from django.test import TestCase
from djangosms.core.transports import Message

def handle(ident, text, time=None, name="script"):
    transport = Message(name)
    return transport.incoming(ident, text, time)

class Gateway(object):
    """Message gateway.

    Use this transport to test communication between two connections.
    """

    def __new__(cls, *args, **kwargs):
        from .transports import Message
        cls = type("Gateway", (cls, Message), {})
        return object.__new__(cls)

    def __init__(self, name, **kwargs):
        self._subscribers = {}
        super(Gateway, self).__init__(name, **kwargs)

    def receive(self, sender, text):
        self._subscribers[sender.ident] = sender
        message = self.incoming(sender.ident, text)
        for request in message.requests.all():
            for response in request.responses.all():
                self.send(response)
        return message

    def send(self, response):
        receiver = self._subscribers[response.connection.ident]
        receiver.receive(response.text)

        # note delivery time
        response.delivery = response.in_response_to.message.time
        response.save()

class Connection(object):
    """Network connection.

    Each connection is configured for a :class:`gateway` with a unique ``ident``
    string.
    """

    def __init__(self, gateway, ident):
        self.gateway = gateway
        self.ident = ident
        self._received = []

    def route(self, text):
        """Routes text."""

        text = text.lstrip("> ")
        assert len(text) <= 160
        return self.gateway.receive(self, text)

    def send(self, text):
        """Sends text."""

        self.route(text)

    def receive(self, text=None):
        """Returns a received message by popping it off the incoming
        stack. If no message was received, the empty string is
        returned.
        """

        if text is None:
            return self._received and self._received.pop(0) or u''
        text = "<<< " + text
        self._received.append(text)

class FormTestCase(TestCase):
    """Adds utility methods for testing forms."""

    default_uri = "test://test"

    @classmethod
    def register_default_user(cls):
        from .models import User
        return User.from_uri(cls.default_uri)

    @classmethod
    def handle(cls, form, text="", uri=None, **kwargs):
        """Handles an incoming message.

        :param handler: Message handler
        :param text: Message body (optional)
        :param uri: Connection URI (defaults to the ``default_uri`` class attribute).

        """

        if uri is None:
            uri = cls.default_uri

        from .models import Incoming
        from datetime import datetime
        time = datetime(1999, 12, 31, 0, 0, 0)
        message = Incoming(text=text, time=time, uri=uri)
        from .models import Connection
        message.connection, created = Connection.objects.get_or_create(uri=uri)
        message.connection.save()
        message.save()
        request = message.requests.create(message=message, text=text)
        response = form(request).handle(**kwargs)
        if response is not None:
            request.reply(response)
        return request
