from django.http import HttpResponse as Response
from .transports import http_event

def incoming(request, name="http+sms"):
    """Incoming messages view.

    The default transport name is ``\"http+sms\"``; to use this view
    with a different transport name, simply define a wrapper view
    function that calls this function with the right ``name``
    argument.

    Example:

      >>> from functools import partial
      >>> kannel_incoming = partial(incoming, name=\"http+kannel\")

    Note that this view is just a paper-thin wrapper around the
    :class:`HTTP <djangosms.core.transports.HTTP>` transport.
    """

    response = Response(u"")
    http_event.send(sender=None, name=name, request=request, response=response)
    return response
