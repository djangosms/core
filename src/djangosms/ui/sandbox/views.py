from urllib import urlencode
from itertools import chain

from django.db.models import Q
from django.db.models.aggregates import Max
from django.db.models.aggregates import Sum
from django.db.models.aggregates import Count
from django.dispatch import Signal
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template.defaultfilters import title
from django.http import HttpResponseRedirect
from django import forms

from djangosms.core.models import Connection
from djangosms.core.models import Message
from djangosms.core.models import Incoming
from djangosms.core.models import Outgoing
from djangosms.core.models import Request
from djangosms.core.models import User

from djangosms.reporter.models import Reporter

class SandboxForm(forms.Form):
    text = forms.CharField(
        label="Text",
        max_length=255,
        widget=forms.TextInput(
            attrs={'size':'40'}),
        required=False,
        )

graduate = Signal(providing_args=["reporter"])

class GraduateFailed(Exception):
    pass

@login_required
def index(req):
    columns = (
        ("id", "#", None),
        ("name", "Name", None),
        ("group", "Location", None),
        ("role", "Role", Max("roles__name")),
        ("activity", "Last activity", Max("connections__messages__time")),
        (None, "Messages", None),
        (None, "Erroneous", None),
        )

    sort_column, sort_descending = _get_sort_info(
        req, default_sort_column="id", default_sort_descending=True)

    search_string = req.REQUEST.get("q", "")

    if search_string == "":
        query = Reporter.objects
    else:
        pks = []
        connections = Connection.objects.filter(uri__icontains=search_string).all()
        for connection in connections:
            try:
                pks.append(connection.reporter.pk)
            except Reporter.DoesNotExist:
                pass

        query = Reporter.objects.filter(
            Q(name__icontains=search_string) |
            Q(pk__in=pks) | Q(group__name__icontains=search_string) |
            Q(roles__name__icontains=search_string)
        )

    form = SandboxForm(req.POST)
    if req.method == 'POST' and form.is_valid():
        pks = req.POST.getlist('reporter')
        text = form.cleaned_data.get('text') or None

        if not req.POST.get('all'):
            query = Reporter.objects.filter(pk__in=pks)

        graduated = []

        if text:
            request = Request(text=text)
            request.save()
        else:
            request = None

        for reporter in query.all():
            try:
                graduate.send(sender=req.user, reporter=reporter)
            except GraduateFailed:
                continue

            if request is not None:
                uri = reporter.most_recent_connection.uri
                message = Outgoing(text=text, uri=uri, in_response_to=request)
                message.save()

            graduated.append(reporter)

        if graduated:
            names = [title(reporter.name) for reporter in graduated]
            separator = [", "] * len(names)
            if len(names) > 1:
                separator[-2] = " and "
            separator[-1] = ""
    
            if request is not None:
                notification_sent_message = " Notification sent: \"%s\"." % text
            else:
                notification_sent_message = ""
    
            req.notifications.add(u"%d reporter(s) graduated: %s.%s" % (
                len(graduated),
                "".join(chain(*zip(names, separator))),
                notification_sent_message,
                ))

        # redirect to GET action
        return HttpResponseRedirect(req.path)

    for name, label, aggregate in columns:
        if aggregate:
            query = query.annotate(**{name: aggregate})

        if name == sort_column:
            sort_desc_string = "-" if sort_descending else ""

    query = query.order_by("%s%s" % (sort_desc_string, sort_column)).all()

    try:
        page = int(req.GET.get('page', '1'))
    except ValueError:
        page = 1

    paginator = Paginator(query, 25).page(page)

    entries = []
    for reporter in paginator.object_list:
        messages = Incoming.objects.filter(
            connection__user__pk=reporter.pk)
        incoming = messages.count()
        erroneous = Request.objects.filter(
            erroneous=True, message__in=messages).count()
        entries.append((reporter, incoming, erroneous))

    return render_to_response("sandbox/index.html", {
        "paginator": paginator,
        "entries": entries,
        "columns": columns,
        "count": query.count(),
        "sort_column": sort_column,
        "sort_descending": sort_descending,
        "search_string": search_string,
        "req": req,
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

