#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *

from .views import dashboard
from .views import static

urlpatterns = patterns(
    '',
    url(r'^$', dashboard),
    url(r'^static$', static),
)

