import re
import doctest

from django.test import TestCase

OPTIONFLAGS = (doctest.ELLIPSIS |
               doctest.NORMALIZE_WHITESPACE)

re_trim = re.compile('[\s\n]+')

def assert_equals(s1, s2, strip=True): # pragma: NOCOVER
    if strip is True and s1 and s2:
        s1 = re_trim.sub(' ', s1.strip(" \n"))
        s2 = re_trim.sub(' ', s2.strip(" \n"))

    assert s1 == s2, "%s != %s." % (repr(s1), repr(s2))

def assert_contains(s1, s2): # pragma: NOCOVER
    assert s2 in s1, "%s does not contain %s." % (repr(s1), repr(s2))

class ModuleTests(TestCase):
    def __new__(self, test):
        return getattr(self, test)()

    @classmethod
    def test_router(cls):
        from djangosms.core import router
        return doctest.DocTestSuite(router)

    @classmethod
    def test_pico(cls):
        from djangosms.core import pico
        return doctest.DocTestSuite(pico)

    @classmethod
    def test_models(cls):
        from djangosms.core import models
        return doctest.DocTestSuite(models)

class DocumentationTest(TestCase): # pragma: NOCOVER
    GLOBS = {
        'assert_equals': assert_equals,
        'assert_contains': assert_contains,
        }

    def __new__(cls, test):
        self = object.__new__(cls)
        self.globs = cls.GLOBS.copy()
        return getattr(self, test)()

    def manuel(func):
        def test(self):
            path = func()

            import manuel.testing
            import manuel.codeblock
            import manuel.doctest
            import manuel.capture
            m = manuel.doctest.Manuel()
            m += manuel.codeblock.Manuel()
            m += manuel.capture.Manuel()

            # create test suite
            return manuel.testing.TestSuite(
                m, path, globs=self.globs,
                setUp=lambda suite: self.setUp(),
                tearDown=lambda suite: self.tearDown())
        return test

    @manuel
    def test_getting_started():
        from os.path import join, dirname
        return join(dirname(__file__), 'getting_started.rst')

    @manuel
    def test_index():
        from os.path import join, dirname
        return join(dirname(__file__), 'index.rst')

    def setUp(self):
        super(DocumentationTest, self).setUp()

        # handle additional setup in a try-except and make sure we
        # tear down the test afterwards
        try:
            from djangosms.core.testing import Gateway
            from djangosms.core.testing import Connection
            from djangosms.core.router import route
            from functools import partial

            table = []
            router = partial(route, table=table)

            transport = Gateway("gateway", router=router)
            self.globs['bob'] = Connection(transport, u"256000000000")
            self.globs['connection'] = Connection(transport, u"256000000000")
            self.globs['routes'] = table
        except:
            self.tearDown()
            del self.globs
            raise
