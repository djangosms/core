from django.http import HttpResponse as Response
from .transports import kannel_event

def kannel(request, name="kannel"):
    """Kannel incoming view.

    The default transport name is "kannel"; to use this view with a
    different transport name, simply define a wrapper view function that
    calls this function with the right ``name`` argument.

    Example:

      >>> from functools import partial
      >>> custom_kannel = partial(kannel, name='custom')

    Note that this view is just a paper-thin wrapper around the
    ``Kannel`` transport.
    """

    response = Response(u"")
    kannel_event.send(sender=name, request=request, response=response)
    return response
