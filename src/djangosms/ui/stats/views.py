from datetime import datetime
from datetime import timedelta
from itertools import chain

from django.db.models import aggregates
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django import forms

from djangosms.stats.models import Group
from djangosms.stats.models import Report
from djangosms.stats.models import ReportKind
from djangosms.stats.models import ObservationKind
from djangosms.stats.models import Observation

def decimal_renderer(value):
    return "%0.f" % value

def timedelta_renderer(value):
    days = int(value)
    if days > 365:
        return "%d years" % (days // 365)
    elif days > 30:
        return "%d months" % (days // 30)
    return "%d days" % days

AGGREGATORS = {
    'avg': aggregates.Avg('value'),
    'sum': aggregates.Sum('value'),
    }

RENDERERS = {
    None: decimal_renderer,
    'timedelta': timedelta_renderer,
    }

TIMEFRAME_CHOICES = (
    (7, "Weekly"),
    (30, "Monthly"),
    (90, "Quarterly"),
    (365, "Yearly"),
    )

class NO_GROUP:
    name = "-"

class TOP_GROUP:
    name = "All"
    pk = ""

    @classmethod
    def get_ancestors(self):
        return ()

class QueryGroup(object):
    pk = ""

    def __init__(self, search_string):
        self.search_string = search_string

    @property
    def name(self):
        return "Query for \"%s\"" % self.search_string

    def get_ancestors(self):
        return (self,)

class StatsForm(forms.Form):
    q = forms.CharField(
        label="Filter",
        max_length=255,
        widget=forms.TextInput(
            attrs={'size':'40'}),
        required=False,
        )

    timeframe = forms.TypedChoiceField(
        choices=TIMEFRAME_CHOICES, coerce=int, initial=7, required=False)

@login_required
def reports(req):
    """Aggregate observations by report and group."""

    form = StatsForm(req.GET)
    days = form.fields['timeframe'].initial
    group = req.GET.get('group', '')
    report = req.GET.get('report', '')
    search_string = req.GET.get('q', '')

    if form.is_valid():
        days = form.cleaned_data.get('timeframe') or days

    now = datetime.now()
    gte = now - timedelta(days=days)

    # set up columns
    sort_column, sort_descending = _get_sort_info(
        req, default_sort_column=None, default_sort_descending=True)

    # determine top-level groups
    if search_string:
        root = QueryGroup(search_string)
        groups = Group.objects.filter(name__icontains=search_string).all()
    elif group:
        root = Group.objects.get(pk=int(group))
        groups = root.get_children().all()
    else:
        root = TOP_GROUP
        first_node = Group.get_first_root_node()
        if first_node is None:
            groups = []
        else:
            groups = list(first_node.get_siblings().all())
        groups.append(NO_GROUP)

    if report:
        report = ReportKind.objects.get(pk=report)
        report_kinds = (report,)
    else:
        report_kinds = ReportKind.objects.all()

    non_trivial_observation_kinds = set()

    by_group = {}
    for group in groups:
        if group is not NO_GROUP:
            tree = Group.get_tree(group)

        by_report_kind = by_group.setdefault(group, {})

        # for each report kind and its observation kinds, compute
        # aggregated values
        if group is not NO_GROUP:
            query = Report.objects.filter(group__in=tree)
        else:
            query = Report.objects.filter(group=None)

        for report_kind in report_kinds:
            by_observation_kind = by_report_kind.setdefault(
                report_kind, {})

            # to-do: this is probably a slow query
            reports = query.filter(
                kind=report_kind,
                source__message__time__gte=gte).all()

            for observation_kind in report_kind.observation_kinds.all():
                observations = Observation.objects.filter(
                    kind=observation_kind, report__in=reports).all()

                if len(observations) == 0:
                    by_observation_kind[observation_kind] = None
                    continue

                non_trivial_observation_kinds.add(observation_kind)

                aggregator = AGGREGATORS[observation_kind.aggregator]
                result = observations.aggregate(aggregator)
                renderer = RENDERERS[observation_kind.renderer]
                aggregate = renderer(result.values()[0])
                by_observation_kind[observation_kind] = aggregate

    if sort_column:
        sort_kind = ObservationKind.objects.get(slug=sort_column)
        group_sort = lambda group: \
                        by_group[group][sort_kind.group][sort_kind]
    else:
        group_sort = None

    # if we're showing more than one report kind, prioritize
    # non-trivial observations; we take the top priority from each
    # report kind and in order of priority fill up to the desired
    # number of observations (columns)
    if len(report_kinds) == 1:
        prioritized = non_trivial_observation_kinds
    else:
        # sort non-trivial observations
        sorted_non_trivial_kinds = sorted(
            non_trivial_observation_kinds,
            key=lambda kind: kind.priority,
            reverse=True)

        # determine non-trivial report kinds
        kinds_for_report_kind = []
        for report_kind in report_kinds:
            kinds = filter(
                sorted_non_trivial_kinds.__contains__,
                report_kind.observation_kinds.all())

            if len(kinds) == 0:
                continue

            kinds_for_report_kind.append((report_kind, kinds))

        # the maximum number of columns must span at least all the
        # non-trivial report kinds
        max_columns = max(8, len(kinds_for_report_kind))
        prioritized = []

        # prioritize
        for report_kind, kinds in kinds_for_report_kind:
            top_priority = kinds[0]
            prioritized.append(top_priority)
            sorted_non_trivial_kinds.remove(top_priority)

        # extend to maximum column length
        missing = max_columns-len(prioritized)
        prioritized.extend(sorted_non_trivial_kinds[:missing])
        assert len(prioritized) <= max_columns

    # set up columns to map report kinds to observation kinds
    columns = []
    for report_kind in sorted(report_kinds):
        observation_kinds = report_kind.observation_kinds.all()
        kinds = filter(prioritized.__contains__, observation_kinds)

        if len(kinds) == 0:
            continue

        filtered = len(kinds) < len(filter(
            non_trivial_observation_kinds.__contains__, observation_kinds))

        columns.append((report_kind, sorted(kinds), filtered))

    for index, timeframe in TIMEFRAME_CHOICES:
        if days == index:
            break

    observations_by_group = [
        (group, tuple(chain(*(
            [value for kind, value in sorted(by_observation_kind.items())
             if kind in prioritized]
            for (report_kind, by_observation_kind) in sorted(
                by_group[group].items())))))
        for group in sorted(
            groups, key=group_sort, reverse=sort_descending)
        ]

    return render_to_response(
        "stats/index.html", {
            'form': form,
            'columns': columns,
            'group': root,
            'report': report,
            'observations_by_group': observations_by_group,
            'sort_column': sort_column,
            'sort_descending': sort_descending,
            'timeframe': timeframe,
            'search_string': search_string,
            },
        RequestContext(req))

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
