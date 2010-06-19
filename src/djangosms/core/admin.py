from django.contrib import admin
from . import models

admin.site.register(models.Connection)
admin.site.register(models.Message)
admin.site.register(models.Route)
admin.site.register(models.Request)
admin.site.register(models.Incoming)
admin.site.register(models.Outgoing)

