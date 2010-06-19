#!/usr/bin/env python
# vim: ai ts=4 sts=4 et sw=4

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

@login_required
def dashboard(request):
    return render_to_response("dashboard.html", {}, RequestContext(request))

def static(request):
    raise ObjectDoesNotExist(request.path)
