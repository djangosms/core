from django.db import models
from djangosms.core.models import User
from djangosms.stats.models import Group

class Role(models.Model):
    """Represents the role of the user.  This may put reporters into
    different roles such as community health workers, supervisors and
    hospital staff."""

    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True, primary_key=True)

class Reporter(User):
    """A reporter."""

    name = models.CharField(max_length=50)
    group = models.ForeignKey(Group, null=True)
    roles = models.ManyToManyField(Role)

    def __unicode__(self):
        return self.name
