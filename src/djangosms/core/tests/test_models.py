from django.test import TestCase

class ConnectionTest(TestCase):
    def test_str(self):
        from djangosms.core.models import Connection
        connection = Connection(uri="test://123")
        self.assertEqual(str(connection), '123')

class MessageTest(TestCase):
    def test_ident(self):
        from djangosms.core.models import Connection
        connection = Connection(uri="foo://bar")
        self.assertEqual(connection.ident, "bar")

    def test_transport(self):
        from djangosms.core.models import Connection
        connection = Connection(uri="foo://bar")
        self.assertEqual(connection.transport, "foo")

    def test_user(self):
        from djangosms.core.models import Connection
        connection = Connection(uri="test://test")
        from djangosms.core.models import Message
        message = Message(connection=connection)
        message.save()
        self.assertEqual(message.user, None)
        from djangosms.core.models import User
        user = User.from_uri("test://test")
        message = Message.objects.get(pk=message.pk)
        self.assertEqual(message.user, user)

class OutgoingTest(TestCase):
    def test_is_reply(self):
        from djangosms.core.models import Connection
        conn1 = Connection(uri="test://1")
        conn1.save()
        conn2 = Connection(uri="test://2")
        conn2.save()

        from djangosms.core.models import Incoming
        from djangosms.core.models import Outgoing
        from djangosms.core.models import Request

        message = Incoming(connection=conn1)
        message.save()

        request = Request(message=message)
        request.save()

        response = Outgoing(connection=conn1, in_response_to=request)
        response.save()
        self.assertTrue(response.is_reply())

        alert = Outgoing(connection=conn2, in_response_to=request)
        alert.save()
        self.assertFalse(alert.is_reply())

        unsolicited = Outgoing(in_response_to=None)
        unsolicited.save()
        self.assertFalse(unsolicited.is_reply())

