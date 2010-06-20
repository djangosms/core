FAQ
===

This is a list of Frequently Asked Questions. Feel free to suggest new
entries!

How do I..
----------

... Log incoming messages to a file?

    Subscribe to the :data:`post_route
    <djangosms.core.transports.post_route>` signal and call the
    :data:`format_incoming <djangosms.core.logging.format_incoming>`
    function::

      import sys

      from djangosms.core.transports import post_route
      from djangosms.core.logging import format_incoming

      def log_incoming(sender=None, **kwargs):
          print sys.stderr, format_incoming(sender)

      post_route.connect(log_incoming)

    The snippet above prints a formatted representation of the
    incoming message, its requests and responses to the ``stderr``
    stream (which is usually routed to a log-file).
