from django.conf.urls.defaults import include
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from django.contrib import admin
from django.contrib.auth.views import login
from django.contrib.auth.views import logout

admin.autodiscover()

from .base import urls as base_urls
from .messages import urls as message_urls
from .stats import urls as stat_urls
from .reporters import urls as reporter_urls

urlpatterns = patterns(
    '',
    url(r'^login$', login),
    url(r'^logout$', logout),
    url(r'^admin/', include(admin.site.urls)),
    ) + \
    base_urls.urlpatterns + \
    message_urls.urlpatterns + \
    stat_urls.urlpatterns + \
    reporter_urls.urlpatterns
