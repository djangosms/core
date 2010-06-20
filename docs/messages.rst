Messages
========

This section describes the message model and related concepts.

Incoming messages
-----------------

When the SMS message protocol is used to communicate *formatted
queries*, it's useful to use the request/response metaphor to wrap our
application logic in the proper abstractions.

Since messages may return multiple such requests, we have a
one-to-many relation between an incoming message and request objects.

.. autoclass:: djangosms.core.models.Incoming
   :noindex:

   .. attribute:: text

      The message body text.

   .. attribute:: requests

      Relation to zero or more request objects.

Each of these requests objects carry multiple responses:

.. autoclass:: djangosms.core.models.Request
   :noindex:

   .. attribute:: responses

      Relation to zero or more response objects. These are
      :term:`replies <reply>` if the ``URI`` attribute is the same as
      the one of the :data:`in_response_to
      <djangosms.core.models.Outgoing.in_response_to>` message
      (applicable only for solicited messages, i.e. those that result
      from an incoming message).

Identification
--------------

Incoming messages are uniquely identified by a URI which is made up
from the transport name and an identification token (ident).

Here's an example of a message arriving on the transport with the name
``'kannel'`` from a mobile subscriber::

  kannel://256703945965

The ``ident`` of this URI is the string ``'256703945965'``.

For each URI in the system, there is a unique :class:``connection
<djangosms.core.models.Connection>`` object. It satisifes the
following relationship::

  connection.message in message.connection.messages

If the peer object corresponds to a registered user, then we can also
access the user object::

  connection.user

Note that one user may be associated to multiple peers. The
``connections`` relation names all registered peers for a particular
user object. Messages have a convenient ``user`` attribute which
returns either ``None`` or a user object. An example of how this can
be used in a message handler::

  def handle(self):
      if self.user is None:
          return u"Must be a registered user."
      else:
          return u"Thank you!"

Routing
-------

Messages are routed by regular expression matching on the routing
table.

Using a callable
----------------

Routing entry on the form: ``(pattern, function)``.

This is the most simple routing form. The function will be passed the
:class:`request <djangosms.core.models.Request>` object and keyword
arguments as returned by the regular expression match' group
dictionary.

The return-value is used as the message reply.

.. _class-based routes:

Using a form class
------------------

The :class:`Form <djangosms.core.router.Form>` class provides a
minimal framework to separate parsing and handling, whilst also adding
a few conveniences:

.. autoclass:: djangosms.core.router.Form
   :noindex:
   :members: user

