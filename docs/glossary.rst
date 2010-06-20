.. _glossary:

============================
Glossary
============================

.. glossary::
   :sorted:

   Form
     Part of a text message input which represents an atomic payload
     (e.g. *user registration* or *incident report*).

   Resolve
     In Django, a resolvable string is a dotted name that maps to a
     global symbol which is directly importable.

   SMS
     Short Message Service

   Reply
     Message response which is sent to the message sender.

   Response
     Message sent in response to an incoming message.

   Transport
     Messages enter and exist the system through transports. An
     example is the :class:`GSM <djangosms.core.transports.GSM`
     transport.

   Request
     In the context of messages, requests are substrings of a message
     that require a response.

   Response
     An outgoing message can be a response to an incoming message.

   Keyword
     Messages that require special formatting sometimes use a syntax
     where a prefix character (e.g. ``"+"`` is succeeded by a keyword
     string such as ``"register"``).
