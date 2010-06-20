from django.db import models
from djangosms.core.models import User

class Policy(models.Model):
    """Defines a user's sandbox policy.

    Default setting is *enabled*.
    """

    user = models.OneToOneField(User)
    enabled = models.BooleanField(default=True)
    last_modified = models.DateTimeField(auto_now=True)
