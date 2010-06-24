from django.db import models
from django.db.models import signals

from djangosms.core.models import User
from djangosms.stats.models import Group
from djangosms.stats.models import Report

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

    def __unicode__(self):
        return self.name
