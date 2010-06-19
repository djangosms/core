from django.db.models import Q
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms

from djangosms.core.models import Incoming
from djangosms.core.models import Connection
from djangosms.core.transports import Message
from djangosms.reporters.models import Reporter

transport = Message("web")

class SendForm(forms.Form):
    text = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'size':'40'})
        )

@login_required
def index(req):
    columns = (("time", "Arrival"),
               ("connection", "Identification"),
               ("text", "Message text"))

    sort_column, sort_descending = _get_sort_info(
        req, default_sort_column="time", default_sort_descending=True)

    sort_desc_string = "-" if sort_descending else ""
    search_string = req.REQUEST.get("q", "")

    query = Incoming.objects.order_by("%s%s" % (sort_desc_string, sort_column))

    if search_string == "":
        query = query.all()

    else:
        query = query.filter(
            Q(text__icontains=search_string) |
            Q(connection__uri__icontains=search_string))

    messages = Paginator(query, 25)

    if req.method == 'POST':
        send_form = SendForm(req.POST)
        if send_form.is_valid():
            if 'send' in req.POST:
                username = req.user.username
            if 'send_as_guest' in req.POST:
                connections = Connection.objects.filter(
                    uri__startswith="%s://guest" % transport.name)
                username = "guest%d" % (len(connections) + 1)
                reporter = Reporter(name="Guest")
                reporter.save()
                reporter.connections.create(uri="%s://%s" % (transport.name, username))

            text = send_form.cleaned_data['text']
            transport.incoming(username, text)
    else:
        send_form = SendForm()

    return render_to_response("messages/index.html", {
        "send_form": send_form,
        "messages": messages,
        "columns": columns,
        "sort_column": sort_column,
        "sort_descending": sort_descending,
        "search_string": search_string
        }, RequestContext(req))


def _get_sort_info(request, default_sort_column, default_sort_descending):
    sort_column = default_sort_column
    sort_descending = default_sort_descending
    if "sort_column" in request.GET:
        sort_column = request.GET["sort_column"]
    if "sort_descending" in request.GET:
        if request.GET["sort_descending"].startswith("f"):
            sort_descending = False
        else:
            sort_descending = True
    return (sort_column, sort_descending)

