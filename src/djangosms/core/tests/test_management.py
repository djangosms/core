import sys
import StringIO

from django.test import TestCase
from contextlib import contextmanager

@contextmanager
def stdout_redirected(new_stdout):
    save_stdout = sys.stdout
    sys.stdout = new_stdout
    try:
        yield None
    finally:
        sys.stdout = save_stdout

class MessagesTest(TestCase):
    def test_dumpmsgs(self):
        from djangosms.core.models import Incoming
        Incoming.from_uri("test://test", text="Test")

        from djangosms.core.management.commands.dumpmsgs import Command

        out = StringIO.StringIO()
        with stdout_redirected(out):
            Command().handle()

        from yaml import load
        messages = load(out.getvalue())

        self.assertTrue(len(messages), 1)
        self.assertTrue("Test" in repr(messages))

    def test_loadmsgs(self):
        from yaml import dump
        from tempfile import NamedTemporaryFile

        f = NamedTemporaryFile()
        f.write(dump([{
            'text': 'Test',
            'uri': 'test://test',
            'time': '2010-05-01T12:34:40+02:00',
            }]))
        f.flush()

        from djangosms.core.management.commands.loadmsgs import Command
        from djangosms.core.models import Incoming

        out = StringIO.StringIO()
        with stdout_redirected(out):
            Command().handle(f.name)

        messages = Incoming.objects.all()

        self.assertTrue(len(messages), 1)
        self.assertTrue(messages[0].text, "Test")
