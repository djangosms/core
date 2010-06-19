#!/usr/bin/env python

import imp
import os
import sys

from django.core.management import execute_from_command_line
from django import conf

try:
    for path in ("settings.py", "sample-settings.py"):
        if os.path.exists(path):
            imp.load_source("settings", path)
            break
    else:
        raise ImportError("settings.py")
except ImportError:
    print >> sys.stderr, (
        "Error: Can't find the file 'settings.py' in "
        "the directory containing %r. It appears "
        "you've customized things.\nYou'll have to "
        "run django-admin.py, passing it your settings "
        "module.\n(If the file settings.py does indeed "
        "exist, it's causing an ImportError somehow.)\n" % \
        __file__)

    sys.exit(1)

if __name__ == "__main__":
    settings = conf.Settings("settings")
    conf.settings.configure(settings)
    execute_from_command_line(sys.argv)
