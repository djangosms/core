import imp
import signal
import functools
from django import conf
from django import utils
from django.core.exceptions import ImproperlyConfigured
from django.core.handlers.wsgi import WSGIHandler
from django.utils.importlib import import_module

# store transports at module-level to prevent gc
_transports = {}

# store old interrupt handlers
_default_handlers = {}

def shutdown(signal, signum, frame): # pragma: NOCOVER
    signal.send(sender=signum)
    _default_handlers[signum](signum, frame)

def make_app(config, settings=None): # pragma: NOCOVER
    # import settings
    imp.load_source("settings", settings)
    settings = conf.Settings("settings")
    conf.settings.configure(settings)
    utils.translation.activate(conf.settings.LANGUAGE_CODE)

    # create WSGI application object
    app = make_app_from_settings(settings)

    # install signal handlers
    from .transports import hangup
    handler = functools.partial(shutdown, hangup)
    _default_handlers[signal.SIGHUP] = signal.signal(signal.SIGHUP, handler)
    _default_handlers[signal.SIGINT] = signal.signal(signal.SIGINT, handler)

    return app

def make_app_from_settings(settings):
    # start transports
    for name, options in getattr(settings, "TRANSPORTS", {}).items():
        try:
            path = options.pop("TRANSPORT")
        except KeyError: # PRAGMA: nocover
            raise ImproperlyConfigured(
                "Unable to configure the '%s' transport. "
                "Must set value for ``TRANSPORT``." % name)

        module_name, class_name = path.rsplit('.', 1)
        module = import_module(module_name)
        factory = getattr(module, class_name)
        _transports[name] = factory(name, options)

    # create handler
    return WSGIHandler()
