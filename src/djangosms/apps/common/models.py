from django.db import models
from djangosms.core.models import Request

class Query(models.Model):
    """Represents an unsolicited user query (i.e. free-form input)."""

    source = models.ForeignKey(Request)
