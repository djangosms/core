from django.test import TestCase

class PatternTest(TestCase):
    def test_match(self):
        from djangosms.core.router import split

        def handler():
            pass

        matches = tuple(split("+echo test", table=(
            (r'^\+echo', handler),
            )))

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][1], handler)

class HandleTest(TestCase):
    def test_signals(self):
        from djangosms.core.router import pre_handle
        from djangosms.core.router import post_handle

        s3 = []
        s4 = []

        def before_handle(sender=None, handler=None, **kwargs):
            s3.append(sender)
            self.assertTrue(handler is handlers.pop(0), handler)
            self.assertEqual(sender.responses.count(), 0)
        pre_handle.connect(before_handle)

        def after_handle(sender=None, error=None, **kwargs):
            s4.append(sender)
            self.assertTrue(error is None, error)
            self.assertEqual(sender.responses.count(), 1)
        post_handle.connect(after_handle)

        from djangosms.core.models import Incoming

        args = []
        def handler1(request, **kwargs):
            args.append((request, kwargs))
            return "1"
        def handler2(request, **kwargs):
            args.append((request, kwargs))
            return "2"

        handlers = [handler1, handler2]

        message = Incoming.from_uri("test://test", text="12")
        message.save()

        from djangosms.core.router import route
        route(message, table=(
            (r'^(?P<input>1)', handler1),
            (r'^(?P<input>2)', handler2),
            ))

        self.assertTrue(len(s3), 1)
        self.assertTrue(len(s4), 1)
        self.assertEqual(len(args), 2)
        self.assertEqual(message.requests.count(), 2)

    def test_formatting_error_means_erroneous(self):
        handled = []
        def check(sender=None, **kwargs):
            handled.append(sender) # pragma: NOCOVER
        from djangosms.core.router import pre_handle
        pre_handle.connect(check)

        from djangosms.core.router import FormatError
        def handler(request, **kwargs):
            raise FormatError("error")

        from djangosms.core.models import Incoming
        message = Incoming.from_uri("test://test", text="")
        message.save()

        from djangosms.core.router import route
        route(message, table=(
            (r'^$', handler),
            ))

        self.assertTrue(len(handled), 1)
        self.assertEqual(message.requests.count(), 1)
        self.assertEqual(message.requests.get().erroneous, True)

    def test_formatting_error_means_dont_handle(self):
        handled = []
        def check(sender=None, **kwargs):
            handled.append(sender) # pragma: NOCOVER
        from djangosms.core.router import pre_handle
        pre_handle.connect(check)

        from djangosms.core.router import FormatError
        from djangosms.core.router import Form

        class Handler(Form):
            def parse(request):
                raise FormatError("error")

            def handle(self):
                raise RuntimeError()

        from djangosms.core.models import Incoming
        message = Incoming.from_uri("test://test", text="")
        message.save()

        from djangosms.core.router import route
        route(message, table=(
            (r'^$', Handler),
            ))

        self.assertTrue(len(handled), 1)
        self.assertEqual(message.requests.count(), 1)
        self.assertEqual(message.requests.get().erroneous, True)

