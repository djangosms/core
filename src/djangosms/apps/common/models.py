from django.db import models
from djangosms.core.models import Request

class Query(models.Model):
    source = models.ForeignKey(Request)
