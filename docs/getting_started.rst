Getting started
===============

In this section you'll learn how to get started with your own project.

Installation
------------

First we need to get the software up and running. In the following we
assume either a system running Linux or Mac OS X.

Make sure you have the right Python interpreter:

.. code-block:: bash

  bash-3.2 $ python
  Python 2.6.1 (r261:67515, Feb 11 2010, 00:51:29)
  [GCC 4.2.1 (Apple Inc. build 5646)] on darwin
  Type "help", "copyright", "credits" or "license" for more information.
  >>>

Check out the software from the repository:

.. code-block:: bash

  bash-3.2 $ git clone http://github.com/djangosms/core.git

Develop the ``DjangoSMS`` egg:

.. code-block:: bash

  bash-3.2 $ sudo easy_install virtualenv
  bash-3.2 $ virtualenv env
  bash-3.2 $ source env/bin/activate
  bash-3.2 $ python setup.py develop

.. note:: The system is compatible with Django 1.2 as of this time of writing.

Run the tests to see if everything works:

.. code-block:: bash

  bash-3.2 $ python manage.py test

You should see the word ``"OK"`` at the end of the command output. If
you see ``"FAILED"`` then something isn't working as it should.

Setting up a new project
------------------------

If you're new to Django, visit the `tutorial
<http://docs.djangoproject.com/en/dev/intro/tutorial01/>`_ to learn
how to create a Django project.

The checkout includes a sample configuration file. Copy it over so you
can adapt it to your project:

.. code-block:: bash

  bash-3.2 $ cp sample-settings.py settings.py

DjangoSMS works like any other Django application. It comes with a set
of applications that you can add to your ``INSTALLED_APPS``::

  INSTALLED_APPS = (
    # common django-apps
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',

    # for testing
    'django_nose',

    # always add this
    'djangosms.core',

    # you'll usually want to add these as well
    'treebeard',
    'djangosms.stats',
    'djangosms.reporters',
    'djangosms.ui',
  )

To start sending and receiving messages you'll also need at least one
message transport (although the system will start even if you do not
configure one). If you have a USB dongle ready, the sample
configuration might work out of the box. Add the following to your
``settings.py`` file::

  TRANSPORTS = {
      'gsm': {
          'TRANSPORT': 'djangosms.core.transports.GSM',
          'DEVICE': '/dev/ttyUSB0',
          }
      }

.. note:: On Mac OS X, the popular Huawei devices usually register themselves as ``"/dev/tty.HUAWEIMobile-Modem"``.

If you've been following along, you should be able to start the system
at this point (don't forget to first set up your database tables using
Django's ``syncdb`` command):

.. code-block:: bash

  bash-3.2 $ paster serve development.ini

You should see an output such as the following:

.. code-block:: bash

  2010-05-20 04:38:02,952 - gsm - INFO - Connected to /dev/tty.HUAWEIMobile-Modem...
  Starting server in PID 81842.
  serving on 0.0.0.0:8080 view at http://127.0.0.1:8080

If you see any other messages being logged, this means there's a
problem talking to your modem.

Adding routes
-------------

You enable message forms by adding an entry in the routing
table. Let's try out the *input* and *register* forms:

.. we extend the ``INSTALLED_APPS`` tuple

  >>> from django.conf import settings as global_settings
  >>> INSTALLED_APPS = global_settings.INSTALLED_APPS

.. code-block:: python

  from djangosms.core.patterns import keyword

  INSTALLED_APPS += (
      'djangosms.apps.common',
      'djangosms.apps.registration',
      )

  ROUTES = (
      (keyword('reg'), 'djangosms.apps.registration.forms.Register'),
      (keyword(r'\w+'), 'djangosms.apps.common.forms.NotUnderstood'),
      (r'^(?P<text>.*)$', 'djangosms.apps.common.forms.Input'),
      )

.. add these routes to the setup

  >>> routes.extend(ROUTES)

Let's try it out! In the following ``>>>`` indicates a message sent to
the system and ``<<<`` indicates a response. You should be able to
repeat the exercise using an actual mobile phone, messaging your
modem.

  >>> +reg john smith

.. -> input

We get the message played back to us::

  <<< Welcome, John Smith. You have been registered.

.. -> output

  >>> bob.send(input)
  >>> assert_equals(bob.receive(), output)

Or, if we send an empty message::

  >>>

.. -> input

This will prompt a helpful response that the message was empty::

  <<< We received an empty message. If this was a mistake, please try again.

.. -> output

  >>> bob.send(input)
  >>> assert_equals(bob.receive(), output)

Writing your own forms
----------------------

You will almost always want to either write your forms or customize
one or more of the forms that come with the system.

Form models all inherit from :class:`djangosms.core.models.Form`. When using
the sequential router, both of the following methods are required:

.. classmethod:: parse(cls, text)
   :noindex:

   Return a non-trivial result if ``text`` parses and a string
   containing any remaining text, or raise :class:`FormatError` to
   indicate a formatting error.

   See :func:`djangosms.core.pico.wrap` for a convenient decorator for parsing
   with the :mod:`picoparse` library.

.. method:: handle(**result)

   Message handler. This method will be passed the parser result. See
   :data:`djangosms.core.models.Incoming.handle`.

For a reference on the :mod:`picoparse` library, see its `readme
<http://github.com/brehaut/picoparse/blob/master/README.markdown>`_
document. Here's a basic example of a parse function that uses the
library::

  from picoparse import remaining
  from picoparse.text import caseless_string
  from picoparse.text import whitespace1

  from djangosms.core.models import Form
  from djangosms.core.router import FormatError
  from djangosms.core.pico import wrap

  class Hello(Form):
      @wrap
      def parse(cls):
          caseless_string("+hello")
          try:
              whitespace1()
              name = "".join(remaining())
          except:
              raise FormatError(u"Input error. Format: +HELLO <name>.")

          return {
              'name': name
              }

To complete the example we would then add a handler method. Add
the following to the class above::

  def handler(self, name=None):
      self.reply("Hello, %s!" % name)

Any remaining text after the parse function completes will be subject
to another parse loop. This means that a single text message may parse
into multiple incoming message objects, each of which are handled
independently, as if they arrived separately. For this reason it is
recommended to use a distinguishable prefix such as ``"+"`` in front
of any one message e.g. ``"+HELLO ..."``.

To guard against remaining text being subject to an additional loop, a
parser may use the following pattern::

  if picoparse.peek():
      raise FormatError(
          "Unexpected text: %s." %
          "".join(picoparse.remaining()))

Note that whitespace is trimmed already before text enters the parser,
so if ``peek()`` returns any non-trivial value, it means there's
remaining text which would subject to another parse.

We could write a form that would catch all punctuation characters::

  from picoparse.text import many1
  from picoparse.text import one_of
  from picoparse.text import partial

  class IgnorePunctuation(Form):
      @wrap
      def parse(cls):
          many1(partial(one_of, ',. '))

      def handle(self):
          pass

This form would simply drop all such input without further action.

Trying it out
-------------

To use the message we first have to enable it::

  FORMS += (
      "Hello",
      )

There are two different approaches to take in terms of testing how
messages work; both have its own merit:

1) Trial and error -- *easy to get started with*
2) Scripted testing -- *more work up front, less work down the road*

The messages that are included with the system are all tested using
automated scripting.

For the first method you can make use of the two included command-line
extensions ``parse`` and ``handle``, corresponding to the required
methods on the message models:

.. code-block:: bash

  bash-3.2 $ python manage.py parse "+ECHO Hello world!"
  Echo: {'echo': u'hello'}

  bash-3.2 $ python manage.py handle "+ECHO Hello world!"
  1/1 2010-05-20T06:40:18.856503
  --> +echo hello
  ---------------
      1/1 script://mborch
      <-- hello

While the ``parse`` command simply shows how the system interprets the
text messages and translates it into one or more messages, the
``handle`` command actually processes it, possibly writing changes to
the database.

To work instead with a scripted test case (recommended), create a file
``tests.py`` and write a unit test for your parser (see
:class:`router.testing.UnitTestCase`) and a form test for your handler
(see :class:`router.testing.FormTestCase`), respectively.

The parser uses a unit test case::

  from djangosms.core.testing import FormTestCase
  from djangosms.core.testing import UnitTestCase

  class ParserTest(UnitTestCase):
      @staticmethod
      def parse(text):
          from ..models.tests import Echo
          return Echo.parse(text)[0]

      def test_echo(self):
          data = self.parse("+ECHO Hello world!")
          self.assertEqual(data, {'echo': 'Hello world!'})

To test your form, it's convenient to use the provided ``handle``
method:

.. automethod:: djangosms.core.testing.FormTestCase.handle
   :noindex:

This makes it easy to write form tests::

  class FormTest(FormTestCase):
      INSTALLED_APPS = FormTestCase.INSTALLED_APPS + (
          'router.tests',
          )

      def test_hello_world(self):
          from djangosms.core.tests import Echo
          message = self.handle(Echo, echo='Hello world!')
          self.assertEqual(message.forms.count(), 1)
          form = message.forms.get().text
          self.assertEqual(form.replies.get().text, 'Hello world!')

Note that if your form needs a registered user (see the section on
:ref:`identification`), you can pass the object as ``user``.

.. warning:: You should never import anything except test cases at module level. Put imports immediately before the symbols are used (inside the test methods).

Run the tests:

.. code-block:: bash

  bash-3.2 $ python setup.py nosetests
