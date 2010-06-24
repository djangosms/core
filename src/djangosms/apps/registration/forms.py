import re
import string

from picoparse import any_token
from picoparse import choice
from picoparse import commit
from picoparse import fail
from picoparse import many1
from picoparse import one_of
from picoparse import optional
from picoparse import partial
from picoparse import peek
from picoparse import remaining
from picoparse import tri
from picoparse.text import whitespace
from picoparse.text import whitespace1

from djangosms.core import pico
from djangosms.core.models import Connection
from djangosms.core.router import FormatError
from djangosms.core.router import Form
from djangosms.stats.models import Report
from djangosms.reporter.models import Reporter

from django.template.defaultfilters import title

class Register(Form):
    """Register with the system.

    New users will register using the format::

       <name>

    At any time, this registration may be updated (change name).

    Users may add a device or handset to their user account by
    providing the identification string (usually a phone number)::

       <phone number>
       #<ident>

    Note that if a phone number is provided, the hash character
    ``\"#\"`` can be omitted.

    """

    @pico.wrap("text")
    def parse(cls):
        result = {}

        @tri
        def ident():
            pico.hash()
            commit()
            return many1(any_token)

        @tri
        def number():
            return many1(partial(one_of, string.digits + ' -+()'))

        ident = optional(partial(choice, ident, number), None)
        if ident is not None:
            result['ident'] = re.sub('[ \-+()]', '', "".join(ident))
        else:
            name = optional(tri(pico.name), None)
            if name is not None:
                result['name'] = name

        whitespace()
        if peek() and not result:
            raise FormatError(
                "We did not understand: %s." % "".join(remaining()))

        return result

    def handle(self, name=None, ident=None):
        if ident is not None:
            # identify user using ``ident`` and add this connection
            try:
                connection = Connection.objects.get(uri__endswith="://%s" % ident)
            except Connection.DoesNotExist:
                pass
            else:
                if connection.user is not None:
                    connection.user.connections.add(
                        self.request.message.connection)
                    self.request.message.connection.save()
                    return "Thank you for your registration."

            return u"Registration failed! We did not find " \
                   "an existing reporter identified by: %s." % ident

        if name is not None:
            if self.user is None:
                created = True
                reporter = Reporter.from_uri(
                    self.request.message.uri, name=name)
            else:
                reporter, created = Reporter.objects.get_or_create(
                    pk=self.user.pk, defaults={'name': name})

            if created:
                Report.from_observations(
                    "registration", new_reporter=1, source=self.request.message)

                return "Welcome, %s. " \
                       "You have been registered." % title(name)
            else:
                reporter.name = name
                reporter.save()

            return "Thank you, %s. You have updated your information." % \
                   title(name)

        if self.user is not None:
            try:
                reporter = Reporter.objects.get(pk=self.user.pk)
            except Reporter.DoesNotExist:
                pass
            else:
                return "Hello, %s. You have already registered." % \
                       title(reporter.name)

        return "Please provide your name to register."
