# vim: ai ts=4 sts=4 et sw=4

from django.conf.urls.defaults import *
from . import views

urlpatterns = patterns(
    '',
    url(r'^reporters/?$', views.index),
    url(r'^whitelist/?$', views.whitelist)
)
