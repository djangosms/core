import cgi
import datetime
import time
import urllib
import functools

from django.test import TransactionTestCase

class MessageTest(TransactionTestCase):
    def test_message_error(self):
        from djangosms.core.tests.transports import Dummy
        from djangosms.core.router import route

        def broken(*args, **kwargs):
            raise RuntimeError("test")

        router = functools.partial(route, table=(
            (r'^\+break', broken),
            ))

        transport = Dummy("dummy", router=router)

        from django.conf import settings
        DEBUG = settings.DEBUG
        try:
            settings.DEBUG = False
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                transport.incoming("test", "+break")

            self.assertEqual(len(w), 1)
            self.assertTrue('RuntimeError' in str(w[0]))
        finally:
            settings.DEBUG = DEBUG

    def test_configuration_error(self):
        from djangosms.core.tests.transports import Dummy
        from djangosms.core.router import route

        router = functools.partial(route, table=(
            (object(),)))

        transport = Dummy("dummy", router=router)

        from django.conf import settings
        DEBUG = settings.DEBUG
        try:
            settings.DEBUG = False
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                transport.incoming("test", "+bad")

            self.assertEqual(len(w), 1)
            self.assertTrue('ImproperlyConfigured' in str(w[0]))
        finally:
            settings.DEBUG = DEBUG

    def test_signals(self):
        from djangosms.core.transports import pre_route
        from djangosms.core.transports import post_route

        s1 = []
        s2 = []

        def before_route(sender=None, **kwargs):
            s1.append(sender)
            self.assertEqual(sender.requests.count(), 0)
        pre_route.connect(before_route)

        def after_route(sender=None, **kwargs):
            s2.append(sender)
            self.assertEqual(sender.requests.count(), 1)
        post_route.connect(after_route)

        from djangosms.core.tests.transports import Dummy
        from djangosms.core.router import route

        def echo(*args, **kwargs):
            return ""

        router = functools.partial(route, table=(
            (r'^\+echo', echo),
            ))

        transport = Dummy("dummy", router=router)
        transport.incoming("test", "+echo")

        self.assertTrue(len(s1), 1)
        self.assertTrue(len(s2), 1)

class HttpTest(TransactionTestCase):
    def tearDown(self):
        import gc
        gc.collect()

        super(HttpTest, self).tearDown()

    @staticmethod
    def _make_http(fetch=None, **kwargs):
        from djangosms.core.transports import HTTP
        if fetch is None:
            def fetch(*args, **kwargs):
                from django.http import HttpResponse as Response
                return Response(u"")

        kwargs.setdefault('send_url', '')

        def echo(form, input):
            return input

        def broken(form):
            raise RuntimeError()

        from djangosms.core.router import route
        router = functools.partial(route, table=(
            (r'^\+echo\s(?P<input>.*)', echo),
            (r'^\+break', broken),
            ))

        transport = HTTP("http+sms", kwargs, router=router)
        transport.fetch = fetch
        return transport

    @property
    def _make_request(self):
        from django.test import Client
        from django.core.handlers.wsgi import WSGIRequest

        class RequestFactory(Client):
            """See Django snippet #963."""

            def request(self, **request):
                environ = {
                    'HTTP_COOKIE': self.cookies,
                    'PATH_INFO': '/',
                    'QUERY_STRING': '',
                    'REQUEST_METHOD': 'GET',
                    'SCRIPT_NAME': '',
                    'SERVER_NAME': 'testserver',
                    'SERVER_PORT': 80,
                    'SERVER_PROTOCOL': 'HTTP/1.1',
                }
                environ.update(self.defaults)
                environ.update(request)
                return WSGIRequest(environ)

        return RequestFactory()

    @property
    def view(self):
        from ..views import incoming
        return incoming

    def test_not_acceptable(self):
        http = self._make_http()
        request = self._make_request.get("/")
        response = self.view(request)
        self.assertEqual(response.status_code, "406 Not Acceptable")

    def test_internal_error_production_mode(self):
        http = self._make_http()
        request = self._make_request.get("/", {
            'from': '456',
            'text': '+break',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        from django.conf import settings
        DEBUG = settings.DEBUG
        try:
            settings.DEBUG = False
            import warnings
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                response = self.view(request)

            self.assertEqual(len(w), 1)
            self.assertTrue('RuntimeError' in str(w[0]))
        finally:
            settings.DEBUG = DEBUG
        self.assertEqual(response.status_code, "200 OK")

    def test_internal_error_debug_mode(self):
        http = self._make_http()
        request = self._make_request.get("/", {
            'from': '456',
            'text': '+break',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        from django.conf import settings
        DEBUG = settings.DEBUG
        try:
            settings.DEBUG = True
            self.assertRaises(RuntimeError, self.view, request)
        finally:
            settings.DEBUG = DEBUG

    def test_message_record(self):
        http = self._make_http()
        request = self._make_request.get("/", {
            'from': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        self.view(request)

        from ..models import Incoming
        results = Incoming.objects.all()
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].text, u"+echo test")
        self.assertNotEqual(results[0].time, None)
        self.assertEquals(results[0].uri, u"http+sms://456")

        from ..models import Outgoing
        outgoing = Outgoing.objects.all()
        self.assertEquals(len(outgoing), 1)
        self.assertEquals(outgoing[0].text, u"test")
        self.assertEquals(outgoing[0].uri, u"http+sms://456")

    def test_message_delivery_success(self):
        request = self._make_request.get("/", {
            'from': '456',
            'text': '+echo test',
            'timestamp': str(time.mktime(
                datetime.datetime(1999, 12, 31).timetuple())),
            })

        query = {}
        def fetch(request=None, **kwargs):
            query.update(cgi.parse_qsl(request.get_full_url()))
            class mock_response:
                status_code = 202
            return mock_response()

        http = self._make_http(fetch=fetch, dlr_url='http://localhost')
        response = self.view(request)

        self.assertNotEqual(query, {})
        args = urllib.urlencode(query)
        self.assertEqual(response.status_code, '200 OK')

        dlr_url = query.pop('dlr-url', "")
        self.assertNotEqual(dlr_url, None)

        delivery = datetime.datetime(2000, 1, 1)
        request = self._make_request.get(
            dlr_url.replace(
                '%d', '1').replace(
                '%T', str(time.mktime(delivery.timetuple()))) + '&' + args)
        response = self.view(request)
        self.assertEqual("".join(response), "")

        # verify delivery record
        from djangosms.core.models import Outgoing
        message = Outgoing.objects.get()
        self.assertFalse(message is None)
        self.assertEqual(message.delivery, delivery)
        self.assertEqual(message.delivered, True)
        self.assertEqual(message.sent, True)
