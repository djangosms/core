from django.db import models
from django.db.models import Q
from django.db.models import signals

from djangosms.core.models import User
from djangosms.core.models import Connection
from djangosms.stats.models import Group
from djangosms.stats.models import Report

def query_reporters(search_string):
    """Search for reporters.

    Multiple terms may be provided using 'OR', e.g. 'John OR James'.
    """

    pks = []

    # split terms if the "OR" operator is used
    terms = [term.strip() for term in search_string.split(' OR ')]

    # look up connection pks that match this query
    pks = Connection.objects.filter(
        reduce(lambda x, y: x | y, [Q(uri__icontains=term) for term in terms])
        ).values_list('user__pk', flat=True)

    return Reporter.objects.filter(
        Q(pk__in=pks) | (
            reduce(
                lambda x, y: x | y,
                [(Q(name__icontains=term) |
                  Q(group__name__icontains=term) |
                  Q(roles__name__icontains=term))
                 for term in terms]
                )))

def on_save_report(sender=None, instance=None, **kwargs):
    if not issubclass(sender, Report):
        return

    if instance.source is None:
        return

    user = instance.source.user
    if user is None:
        return

    try:
        reporter = Reporter.objects.get(pk=user.pk)
    except Reporter.DoesNotExist:
        return

    if instance.group is not None or reporter.group is None:
        return

    instance.group = reporter.group
    instance.save()

signals.post_save.connect(on_save_report)

class Role(models.Model):
    """Represents the role of the user.  This may put reporters into
    different roles such as community health workers, supervisors and
    hospital staff."""

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)

    def __unicode__(self):
        return self.name

class Reporter(User):
    """A reporter."""

    name = models.CharField(max_length=50)
    group = models.ForeignKey(Group, null=True)
    roles = models.ManyToManyField(Role)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name
