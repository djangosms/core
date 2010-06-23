from urllib import urlencode

from django.db.models import Q
from django.db.models import aggregates
from django.core.paginator import Paginator
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django import forms

from djangosms.core.models import Connection
from djangosms.core.models import Incoming
from djangosms.core.models import Outgoing
from djangosms.core.models import User

from djangosms.reporter.models import Reporter

class SendForm(forms.Form):
    text = forms.CharField(
        label="Text",
        max_length=255,
        widget=forms.TextInput(
            attrs={'size':'40'}),
        required=False,
        )

@login_required
def index(req):
    form = SendForm(req.POST)
    if req.method == 'POST' and form.is_valid():
        text = form.cleaned_data.get('text') or None
        reporters = req.POST.getlist('reporter')

        if text is None:
            req.notifications.add(u"No text was submitted; ignored.")
        else:
            for pk in reporters:
                user = User.objects.get(pk=pk)
                uri = user.most_recent_connection.uri
                message = Outgoing(text=text, uri=uri)
                message.save()

            req.notifications.add(
                u"Message sent to %d recipient(s)." % len(reporters))

        # redirect to GET action
        return HttpResponseRedirect(req.path)

    columns = (
        ("id", "#", None),
        ("name", "Name", None),
        ("group", "Location", None),
        ("role", "Role", "roles__name"),
        ("activity", "Last activity", "connections__messages__time"),
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

    for name, title, aggregate in columns:
        if name != sort_column:
            continue

        if aggregate:
            query = query.annotate(**{name: aggregates.Max(aggregate)})

        sort_desc_string = "-" if sort_descending else ""
        query = query.order_by("%s%s" % (sort_desc_string, name)).all()

        break

    entries = []
    
    try:
        page = int(req.GET.get('page', '1'))
    except ValueError:
        page = 1

    paginator = Paginator(query, 25).page(page)

    for reporter in paginator.object_list:
        messages = Incoming.objects.filter(
            connection__in=reporter.connections.all())

        if messages:
            message = messages[0]
        else:
            message = None

        entries.append((reporter, message))

    return render_to_response("reporters/index.html", {
        "entries": entries,
        "paginator": paginator,
        "columns": columns,
        "sort_column": sort_column,
        "sort_descending": sort_descending,
        "search_string": search_string,
        "req": req
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

