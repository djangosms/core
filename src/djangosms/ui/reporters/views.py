from django.db.models.aggregates import Max
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse as Response
from django import forms

from djangosms.core.models import Message
from djangosms.core.models import Outgoing
from djangosms.core.models import Request

from djangosms.reporter.models import Reporter
from djangosms.reporter.models import query_reporters

class SendForm(forms.Form):
    text = forms.CharField(
        label="Text",
        max_length=255,
        widget=forms.TextInput(
            attrs={'size':'40'}),
        required=False,
        )

def whitelist(req):
    response = ''
    if (req.META['SERVER_NAME'] == 'localhost' or 
        req.META['SERVER_NAME'] == '127.0.0.1' or 
        req.META['SERVER_NAME'] == '0.0.0.0' or 
        req.META['SERVER_NAME'] == 'cvs'):
        for reporter in Reporter.objects.filter(active=True):
            for connection in reporter.connections.all():
                try:
                    response += str(int(connection.ident)) + "\n"
                except ValueError:
                    pass
    return Response(response,mimetype="text/plain")

@login_required
def index(req):
    columns = (
        ("id", "#", "id", None),
        ("name", "Name", "name", None),
        ("group", "Location", "group__name", None),
        ("role", "Role", "roles__name", None),
        ("activity", "Last activity", "activity", Max("connections__messages__time")),
        (None, "Message", None, None),
        )

    sort_column, sort_descending = _get_sort_info(
        req, default_sort_column="id", default_sort_descending=True)

    search_string = req.REQUEST.get("q", "")

    if search_string == "":
        query = Reporter.objects
    else:
        query = query_reporters(search_string)

    query = query.filter(active=True)

    form = SendForm(req.POST)
    if req.method == 'POST' and form.is_valid():
        text = form.cleaned_data.get('text') or None
        reporters = req.POST.getlist('reporter')

        if text is None:
            req.notifications.add(u"No text was submitted; ignored.")
        else:
            if not req.POST.get('all'):
                query = Reporter.objects.filter(pk__in=reporters)

            request = Request(text=text)
            request.save()

            for reporter in query.all():
                uri = reporter.most_recent_connection.uri
                message = Outgoing(text=text, uri=uri, in_response_to=request)
                message.save()

            req.notifications.add(
                u"Message sent to %d recipient(s)." % query.count())

        # redirect to GET action
        return HttpResponseRedirect(req.path)

    for name, title, sorting, aggregate in columns:
        if aggregate:
            query = query.annotate(**{name: aggregate})

        if name == sort_column:
            sort_desc_string = "-" if sort_descending else ""
            query = query.order_by("%s%s" % (sort_desc_string, sorting)).all()

    entries = []

    try:
        page = int(req.GET.get('page', '1'))
    except ValueError:
        page = 1

    paginator = Paginator(query, 25)
    count = paginator.count
    paginator = paginator.page(page)

    for reporter in paginator.object_list:
        try:
            message = Message.objects.filter(
                connection__in=reporter.connections.all()).latest()

        except Message.DoesNotExist:
            message = None
            is_outgoing_message = 0

        else:
            is_outgoing_message = Outgoing.objects.filter(
                    pk=message.pk).count()

        entries.append((reporter, message, is_outgoing_message))

    return render_to_response("reporters/index.html", {
        "entries": entries,
        "paginator": paginator,
        "columns": columns,
        "sort_column": sort_column,
        "sort_descending": sort_descending,
        "search_string": search_string,
        "req": req,
        "count" : count
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

