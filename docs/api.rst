API Reference
==============

This is a reference on public classes and functions in the system.

This section details the API of the base system.

Models
~~~~~~

.. automodule:: djangosms.core.models

  .. autoclass:: Message
     :members: user

     .. attribute:: text

        The message body string.

     .. attribute:: time

        The time a message was received.

  .. autoclass:: Connection
     :members:   transport, ident

     .. attribute:: user

        Relation to a :class:`user <djangosms.core.models.User>`
        object, if applicable. Messages always have a connection
        object, but only messages sent from registered users have a
        user object.

  .. autoclass:: User

     .. attribute:: connections

        Set of connections which authenticate this user object.

  .. autoclass:: Incoming

     .. attribute:: requests

        The requests that were routed from this message.

  .. autoclass:: Outgoing
     :members:   delivered, is_reply, sent

     .. attribute:: delivery

        The date when this message was delivered. This field is
        ``None`` unless a delivery confirmation receipt was provided
        to the transport.

     .. attribute:: in_response_to

        The request to which this is a response, or ``None`` if
        unsolicited.

  .. autoclass:: Request
     :members:   reply, respond

     .. attribute:: route

        Record of the :class:`request route <Route>` (optional).

     .. attribute:: text

        The request input string.

     .. attribute:: message

        The incoming message object from which this request was
        routed.

     .. attribute:: erroneous

        Indicates whether the request was marked as erroneous during
        parsing (if a :class:`FormatError
        <djangosms.core.router.FormatError>` exception was raised).

     .. attribute:: responses

        Responses given for this request (see :data:`outgoing
        <rapidsms.core.models.Outgoing>`).

Patterns
~~~~~~~~

.. automodule:: djangosms.core.patterns

   .. autofunction:: keyword

Router
~~~~~~

.. automodule:: djangosms.core.router
   :members: route, split

   .. autoclass:: Form

   .. autoclass:: FormatError

Signals
-------

.. data:: djangosms.core.router.pre_handle(sender=None, handler=None, error=None)

   Called immediately *before* a request is handled (but after it's been
   saved).

   This signal sends an additional ``handler`` argument which is the
   callable that the request will be handled by.

.. data:: djangosms.core.router.post_handle(sender=None, error=None)

   Called immediately *after* a request was handled. If an exception was
   raised, it will be passed as ``error`` (and re-raised immediately
   after this signal is sent).

Pico
~~~~

The :mod:`djangosms.core.pico` module also contains a number of utility parser
functions that you are encouraged to make use of:

.. automodule:: djangosms.core.pico

   .. function:: comma()

      Parses a comma.

   .. autofunction:: date

   .. function:: dot()

      Parses a period (dot).

   .. function:: digit()

      Parses a single digit.

   .. function:: digits()

      Parses one or more digits.

   .. autofunction:: floating

   .. autofunction:: identifier([first, consecutive, must_contain])

   .. autofunction:: name

   .. autofunction:: one_of_strings

   .. autofunction:: separator(parser=comma)

   .. autofunction:: tags

   .. autofunction:: timedelta

Transports
~~~~~~~~~~

.. automodule:: djangosms.core.transports

   .. autoclass:: Transport(name[, options])
      :members:

   .. autoclass:: djangosms.core.transports.Message
      :members:   incoming, router

Signals
-------

.. data:: djangosms.core.transports.pre_route(sender=None)

   Called *before* an incoming message is parsed.

   The ``sender`` of this signal is an
   :class:`djangosms.core.models.Incoming` instance.

   Changing the value of the ``text`` attribute of the incoming
   message object in this step will directly control the input to the
   routing table.

.. data:: djangosms.core.transports.post_route(sender=None)

   Called *after* an incoming message was parsed.

GSM
---

.. autoclass:: djangosms.core.transports.GSM

HTTP
----

.. autoclass:: djangosms.core.transports.HTTP
   :members:   fetch, handle

.. autofunction:: djangosms.core.views.incoming


.. _testing:

Logging
~~~~~~~

.. automodule:: djangosms.core.logging

   .. autofunction:: format_incoming

Testing
~~~~~~~

Django's test runner is used with the :mod:`django_nose` extension::

  TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

Most importantly, the use of the :mod:`nose` testing library allows us
to put tests into separate modules under the ``tests`` directory.

Coverage
--------

The :mod:`nose` package comes with integration to
:mod:`coverage`. It's a separate package that must first be
installed::

  $ easy_install coverage

Run tests using the script::

  $ coverage run manage.py test

This will write a coverage report to ``.coverage`` in the local
directory. To print out a summary to the terminal::

  $ coverage report

It's usually desirable to restrict output to your working modules. In
the default checkout these all resides under the ``src``
subdirectory::

  $ coverage report -m $(find src -name '*.py')

To exclude the user interface app (currently untested)::

  $ coverage report -m --omit src/djangosms/ui $(find src -name '*.py')

Form tests
----------

This is a convenience test class for testing :class:`form
<djangosms.core.router.Form>` classes.

.. autoclass:: djangosms.core.testing.FormTestCase()

Gateway
-------

To test communication between multiple peers and the system, the
following framework is available.

.. autoclass:: djangosms.core.testing.Gateway

.. autoclass:: djangosms.core.testing.Connection

   .. automethod:: djangosms.core.testing.Connection.send(text)

   .. automethod:: djangosms.core.testing.Connection.receive()

Configure it this way::

  gateway = Gateway("gateway")
  bob = Connection(gateway, u"bob")

Bob can now send and receive messages::

  >>> bob.send("+ECHO Hello world+")
  >>> bob.receive()
  'Hello world'

