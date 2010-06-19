from django.test import TestCase
from djangosms.core.testing import FormTestCase

class ParserTest(TestCase):
    @staticmethod
    def _parse(text):
        from .forms import Register
        return Register().parse(text=text)

    def test_empty(self):
        self.assertEquals(self._parse(""), {})

    def test_remaining(self):
        self.assertEquals(self._parse("Bob +reg"), {'name': u'Bob'})

    def test_name(self):
        self.assertEquals(self._parse("Bob"), {'name': u'Bob'})

    def test_ident(self):
        self.assertEquals(self._parse("#123"), {'ident': '123'})
        self.assertEquals(self._parse("123"), {'ident': '123'})
        self.assertEquals(self._parse("1-2-3"), {'ident': '123'})
        self.assertEquals(self._parse("1 2 3"), {'ident': '123'})
        self.assertEquals(self._parse("#"), None)

class HandlerTest(FormTestCase):
    @classmethod
    def _register(cls, **kwargs):
        from .forms import Register
        return cls.handle(Register, **kwargs)

    def test_initial_registration(self):
        self._register(name="foo")
        from djangosms.reporters.models import Reporter
        self.assertEqual(Reporter.objects.get().name, "foo")

    def test_report(self):
        self._register(name="foo")
        from djangosms.stats.models import Observation
        self.assertEqual(Observation.objects.count(), 1)

    def test_empty_request(self):
        self._register(name="foo")
        request = self._register()
        self.assertTrue("foo" in request.responses.get().text.lower())

    def test_inquire_for_ident_but_not_registered(self):
        self._register()
        request = self._register()
        from djangosms.reporters.models import Reporter
        self.assertEqual(Reporter.objects.count(), 0)
        self.assertFalse(str(request.message.connection.ident) in \
                         request.responses.get().text)

    def test_registration_update(self):
        self._register(name="foo")
        self._register(name="bar")
        from djangosms.reporters.models import Reporter
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_then_update(self):
        request = self._register(name="foo")
        from djangosms.reporters.models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        self._register(uri="test://new", ident=request.message.connection.ident)
        self.assertEqual(Reporter.objects.count(), 1)
        self._register(uri="test://new", name="bar")
        self.assertEqual(Reporter.objects.get().name, "bar")

    def test_register_new_device_but_not_found(self):
        self._register(name="foo")
        from djangosms.reporters.models import Reporter
        self.assertEqual(Reporter.objects.count(), 1)
        request = self._register(uri="test://new", ident="new")
        self.assertEqual(request.message.user, None)
        self.assertTrue('new' in request.responses.get().text.lower())
