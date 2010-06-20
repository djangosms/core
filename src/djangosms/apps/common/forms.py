from picoparse import remaining

from djangosms.core import pico
from djangosms.core.router import Form
from djangosms.core.router import FormatError

from .models import Query

class NotUnderstood(Form):
    def parse(self, text=None):
        raise FormatError(
            "We did not understand your message: %s." % (
                (text or "").strip() or "(empty)"))

class Input(Form):
    """Free-form input."""

    @pico.wrap('text')
    def parse(self):
        return {
            'text': "".join(remaining())
            }

    def handle(self, text=None):
        if not text.strip():
            return "We received an empty message. If this was a mistake, " \
                   "please try again."
        else:
            Query(source=self.request).save()
            return "We have received your input. Thank you."
