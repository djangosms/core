from djangosms.core.patterns import keyword

# import yaml, this basically checks that it is installed, we do this so that 
# fixtures in yaml format don't fail silently when yaml isn't installed.
import yaml

DEBUG = True

ROOT_URLCONF = "djangosms.ui.urls"

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'default.db'
    }
}

# the prefix to use for our keywords
KEYWORD_PREFIX = '+'

ROUTES = (
    # user registration; from this route and down, users must be registered
    (keyword('register|reg'), 'djangosms.apps.registration.forms.Register'),
    (r'^', 'djangosms.apps.registration.forms.MustRegister'),

    # unknown keyword
    (keyword(r'\w+'), 'djangosms.apps.common.forms.NotUnderstood'),

    # free-form text input
    (r'^(?P<text>.*)$', 'djangosms.apps.common.forms.Input'),
    )

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'treebeard',
    'django_nose',
    'djangosms.core',
    'djangosms.stats',
    'djangosms.reporter',
    'djangosms.ui',
    'djangosms.apps.common',
    'djangosms.apps.registration',
    )

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_notify.middleware.NotificationsMiddleware',
    )

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.core.context_processors.auth',
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.csrf",
    "django_notify.context_processors.notifications",
    )

LOGIN_URL = "/login"
LOGIN_REDIRECT_URL = "/"
