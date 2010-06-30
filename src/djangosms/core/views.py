from datetime import datetime

from django.http import HttpResponse as Response
from .transports import http_event

from django.contrib.auth import authenticate
from djangosms.core.testing import handle
from djangosms.core.transports import Message

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

def loadmsg(request):
    user = request.POST['username']
    passwd = request.POST['password']
    user = authenticate(username=user, password=passwd)
    if user is not None:
        text = request.POST['text']
        sender = request.POST['from']
        timestamp = request.POST['timestamp']
        timestamp = datetime.fromtimestamp(
                float(timestamp))
        transport = Message('http+sms')
        transport.incoming(sender, text, timestamp, True)
    return Response()