from django.db import models

from djangosms.core.models import Request
from treebeard.mp_tree import MP_Node

RENDERERS = (
    ('timedelta', 'Time delta'),
    ('datetime', 'Date and time'),
    )

AGGREGATORS = (
    ('avg', 'Average'),
    ('sum', 'Sum'),
    )

class GroupKind(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)
    description = models.CharField(max_length=255, null=True)

    def __unicode__(self):
        return self.name

class Group(MP_Node):
    name = models.CharField(max_length=50, db_index=True)
    kind = models.ForeignKey(GroupKind)
    node_order_by = ['name']

    def __init__(self, *args, **kwargs):
        slug = kwargs.pop("slug", None)
        if slug is not None:
            kwargs.setdefault("kind", GroupKind.objects.get(slug=slug))
        super(Group, self).__init__(*args, **kwargs)

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def __unicode__(self):
        return "%s %s" % (self.name, self.kind.name)

    def get(self):
        return type(self).objects.get(pk=self.pk)

class ReportKind(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)
    description = models.CharField(max_length=255, null=True, blank=True)

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def __eq__(self, other):
        return self.slug == getattr(other, "slug", other)

    def __ne__(self, other):
        return self.slug != getattr(other, "slug", other)

class Report(models.Model):
    source = models.ForeignKey(Request, null=True)
    group = models.ForeignKey(Group, null=True)
    kind = models.ForeignKey(ReportKind, db_index=True)

    class Meta:
        ordering = ['-id']

    def __init__(self, *args, **kwargs):
        slug = kwargs.pop("slug", None)
        if slug is not None:
            kwargs.setdefault("kind", ReportKind.objects.get(slug=slug))
        super(Report, self).__init__(*args, **kwargs)

    def __unicode__(self):
        if self.group is not None:
            return "%s @ %s" % (self.kind.name, self.group)
        else:
            return self.kind.name

    @classmethod
    def from_observations(cls, slug, source=None, group=None, **observations):
        """Create a report from a set of observations.

        :param slug: Report kind slug.
        :param source: The source from which this report originated.
        :param group: The group that this report belongs to.

        In this example we'll set up an Epidemiology report for
        sightings of Malaria and Tuberculosis.

        >>> kind = ReportKind(slug='epi', name='Epidemiology')
        >>> kind.save()

        >>> ObservationKind(slug='ma', group=kind, name='Malaria').save()
        >>> ObservationKind(slug='tb', group=kind, name='Tuberculosis').save()

        You can specify both the report kind and the observations using the slug string.

        >>> report = Report.from_observations('epi', ma=10, tb=20)
        >>> report.observations.count()
        2

        Reports created this way or automatically saved.

        >>> report.pk is not None
        True

        """

        report = Report(slug=slug, source=source, group=group)
        report.save()

        for slug, value in observations.items():
            report.observations.create(slug=slug, value=value)

        return report

class ObservationKind(models.Model):
    slug = models.SlugField(unique=True, primary_key=True)
    name = models.CharField(max_length=50)
    abbr = models.CharField(max_length=10, null=True)
    group = models.ForeignKey(
        ReportKind, related_name='observation_kinds',
        db_index=True)
    aggregator = models.CharField(max_length=20, choices=AGGREGATORS, default='sum')
    renderer = models.CharField(max_length=20, choices=RENDERERS, null=True)
    description = models.CharField(max_length=255, null=True, blank=True)
    priority = models.IntegerField(default=1, db_index=True)

    def __lt__(self, other):
        return self.name < other.name

    def __gt__(self, other):
        return self.name > other.name

    def __eq__(self, other):
        return self.slug == other.slug

    def __ne__(self, other):
        return self.slug != other.slug

class Observation(models.Model):
    value = models.DecimalField(max_digits=20, decimal_places=10)
    kind = models.ForeignKey(ObservationKind, db_index=True)
    report = models.ForeignKey(Report, related_name='observations', db_index=True)

    class Meta:
        ordering = ['-id']

    def __init__(self, *args, **kwargs):
        slug = kwargs.pop("slug", None)
        if slug is not None:
            kwargs.setdefault("kind", ObservationKind.objects.get(slug=slug))
        super(Observation, self).__init__(*args, **kwargs)

    def __unicode__(self):
        return "%s=%s" % (self.kind.name, self.value)
