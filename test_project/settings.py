# Python
import collections
import email.utils
import logging
import os
import sys

# Django-Environ
import environ


##############################################################################
# Initialize settings from environment variables and .env files
##############################################################################

class Env(environ.Env):

    def search_path(self, var, default=environ.Env.NOTSET, **kwargs):
        value = self.get_value(var, default=default)
        return list(map(environ.Path, [x for x in value.split(os.pathsep) if x]))


# Absolute path to the directory containing this project.
root = environ.Path(__file__, is_file=True)
BASE_DIR = root()

DOKKU = bool(os.environ.get('DOKKU_APP_TYPE', False))

# Determine if running from checkout.
DEVELOPMENT = False
dev_dir = root
while True:
    if os.path.exists(str(dev_dir.path('.git'))) and not DOKKU:
        DEVELOPMENT = True
        break
    if dev_dir == dev_dir - 1:
        break
    dev_dir = dev_dir - 1

# Initialize from environment variables.
env = Env(
    DEBUG=(bool, DEVELOPMENT),
)

if DEVELOPMENT:
    default_env_path = root('..', '.env')
    default_data_path = root('local')
else:
    default_env_path = ''
    default_data_path = root('local')

# Path(s) of .env files to load.
ENV_PATH = env.search_path('ENV_PATH', default=default_env_path)

# OS environment variables take precedence over variables from .env files.
# First file loaded takes precedence, since env is updated using set_default().
for env_path in ENV_PATH:
    env.read_env(str(env_path))

# Create default .env file if needed (for default SECRET_KEY).
env_defaults = collections.OrderedDict()
if not env.str('SECRET_KEY', ''):
    from django.utils.crypto import get_random_string
    secret_key_chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    env_defaults['SECRET_KEY'] = get_random_string(50, secret_key_chars)
if not env.str('DATABASE_URL', ''):
    env_defaults['DATABASE_URL'] = 'psql://user:pass@127.0.0.1/database'
if not env.str('REDIS_URL', ''):
    env_defaults['REDIS_URL'] = 'redis://127.0.0.1:6379/2'
if env_defaults and ENV_PATH and DEVELOPMENT:
    default_env_path = str(ENV_PATH[0])
    if not os.path.exists(os.path.dirname(default_env_path)):
        os.makedirs(os.path.dirname(default_env_path))
    with open(default_env_path, 'a') as env_file:
        for name, value in env_defaults.items():
            env_file.write('{}=\'{}\'\n'.format(name, value))
            env.ENVIRON[name] = value

DATA_DIR = env.path('DATA_DIR', default=default_data_path)()
LOG_DIR = env.path('LOG_DIR', default=environ.Path(DATA_DIR)('logs'))()
EMAIL_DIR = env.path('EMAIL_DIR', default=environ.Path(DATA_DIR)('emails'))()

##############################################################################
# Site/Security Settings
##############################################################################

SITE_ID = env.int('SITE_ID', default=1)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', cast=str, default=['*'])
SECRET_KEY = env.str('SECRET_KEY')
X_FRAME_OPTIONS = 'SAMEORIGIN'

##############################################################################
# Internationalization/Localization
##############################################################################

LANGUAGE_CODE = env.str('LANGUAGE_CODE', default='en-us')
TIME_ZONE = env.str('TIME_ZONE', default='America/New_York')
USE_I18N = env.bool('USE_I18N', default=True)
USE_L10N = env.bool('USE_L10N', default=True)
USE_TZ = env.bool('USE_TZ', default=True)
DATETIME_FORMAT = env.str('DATETIME_FORMAT', default='Y-m-d H:i:s T')
SHORT_DATETIME_FORMAT = env.str('SHORT_DATETIME_FORMAT', default='m/d/Y P')

##############################################################################
# Static and Media File Settings
##############################################################################

STATIC_URL = env.str('STATIC_URL', default='/static/')
MEDIA_URL = env.str('MEDIA_URL', default='/media/')

if DEVELOPMENT:
    default_static_root = root('public', 'static')
    default_media_root = root('public', 'media')
else:
    default_static_root = environ.Path(DATA_DIR)('public', 'static')
    default_media_root = environ.Path(DATA_DIR)('public', 'media')

STATIC_ROOT = env.path('STATIC_ROOT', default=default_static_root)()
MEDIA_ROOT = env.path('MEDIA_ROOT', default=default_media_root)()

STATICFILES_DIRS = (
    # root('static'),
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

##############################################################################
# Middleware Settings
##############################################################################

MIDDLEWARE = [
    # 'django.middleware.cache.UpdateCacheMiddleware', # Must always be first.
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware', # Must always be last.
]

##############################################################################
# Template Settings
##############################################################################

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            root('templates'),
        ],
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
            'loaders': [
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ],
            'debug': env('DEBUG'),
        },
    },
]

##############################################################################
# Apps
##############################################################################

ROOT_URLCONF = 'test_project.urls'

WSGI_APPLICATION = 'test_project.wsgi.application'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django_celery_beat',
    'django_celery_results',
    'django_extensions',
    'site_utils',
    'celery_task_plus',
    'test_project.test_app',
)

##############################################################################
# Database Settings
##############################################################################

DATABASES = {
    'default': env.db_url(),
}

REDIS_URL = env.url('REDIS_URL').geturl()

##############################################################################
# Cache Settings
##############################################################################

CACHES = {
    'default': env.cache_url(default=REDIS_URL),
}

CACHE_MIDDLEWARE_SECONDS = 30

##############################################################################
# Login/Registration Settings
##############################################################################

LOGIN_REDIRECT_URL = '/admin/'

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

##############################################################################
# Celery Settings
##############################################################################

CELERY_BROKER_URL = env.url('CELERY_BROKER_URL', default=REDIS_URL).geturl()

CELERY_ENABLE_UTC = env.bool('CELERY_ENABLE_UTC', default=True)
CELERY_TIME_ZONE = env.str('CELERY_TIME_ZONE', default=TIME_ZONE)

CELERY_RESULT_BACKEND = 'django-db'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_STORE_ERRORS_EVEN_IF_IGNORED = True

CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)

CELERY_SEND_EVENTS = True
CELERY_SEND_TASK_SENT_EVENT = True

CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_BEAT_SCHEDULE = {
    # 'app.task_name': {
    #     'task': 'app.task_name',
    #     'args': (),
    #     'kwargs': {},
    #     'schedule': datetime.timedelta(seconds=5),
    #     'last_run_at': datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),  # Run on startup.'
    #     'enabled': True,
    # },
}

##############################################################################
# Email Settings
##############################################################################

EMAIL_FILE_PATH = None
EMAIL_CONFIG = env.email_url('EMAIL_URL', default='filemail://localhost/{}'.format(EMAIL_DIR))
vars().update(EMAIL_CONFIG)

DEFAULT_FROM_EMAIL = env.str('DEFAULT_FROM_EMAIL', default='no-reply@localhost')
SERVER_EMAIL = env.str('SERVER_EMAIL', default=DEFAULT_FROM_EMAIL)
EMAIL_SUBJECT_PREFIX = env.str('EMAIL_SUBJECT_PREFIX', default='[CeleryTaskPlus - Dev] ')

ADMINS = env.list('ADMINS', cast=email.utils.parseaddr, default=[])
MANAGERS = env.list('MANAGERS', cast=email.utils.parseaddr, default=ADMINS)

##############################################################################
# Logging Settings
##############################################################################

# Add log level for trace.
if not hasattr(logging, 'TRACE'):
    logging.TRACE = 5
    logging.addLevelName(logging.TRACE, 'TRACE')

    def trace(self, message, *args, **kwargs):
        if self.isEnabledFor(logging.TRACE):
            self._log(logging.TRACE, message, args, **kwargs)

    logging.Logger.trace = trace

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)-8s %(asctime)s %(module)s %(process)d %(thread)d %(message)s',
        },
        'simple': {
            'format': '%(levelname)-8s %(message)s',
        },
        'custom': {
            'format': '%(levelname)-8s %(asctime)s %(name)s %(process)d %(thread)d %(message)s',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'custom',
            'filters': ['require_debug_false'],
        },
        'debug_console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'custom',
            'filters': ['require_debug_true'],
        },
        'mail_admins': {
            'level': 'WARNING',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['debug_console'],
            'level': 'INFO',
        },
        'django.db.backends': {
            'handlers': ['null'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['debug_console', 'mail_admins'],
            'propagate': False,
        },
        'django.security': {
            'handlers': ['debug_console', 'mail_admins'],
            'propagate': False,
        },
        'py.warnings': {
            'handlers': ['debug_console'],
        },
        'test_project': {
            'handlers': ['console', 'debug_console'],
            'level': 'DEBUG',
            'filters': [],
            'propagate': False,
        },
    },
}

##############################################################################
# Debug/Development Settings
##############################################################################

DEBUG = env('DEBUG')

# Django debug toolbar settings
try:
    import debug_toolbar  # noqa
    INSTALLED_APPS += ('debug_toolbar',)
    MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
except ImportError:
    pass

DEBUG_TOOLBAR_PATCH_SETTINGS = False
DEBUG_TOOLBAR_CONFIG = {
    'JQUERY_URL': '/static/admin/js/vendor/jquery/jquery.js',
}

INTERNAL_IPS = ('127.0.0.1',)

RUNSERVER_DEFAULT_ADDR = env.str('RUNSERVER_DEFAULT_ADDR', default='127.0.0.1')
RUNSERVER_DEFAULT_PORT = str(env.int('RUNSERVER_DEFAULT_PORT', default=8035))

try:
    import ipython  # noqa
    SHELL_PLUS = 'ipython'
except ImportError:
    pass

# Set testing flag if invoked for testing.
TESTING = bool(sys.argv[1:2] == ['test'] or any([x.endswith('py.test') for x in sys.argv[0:1]]))
TESTING = env.bool('TESTING', default=TESTING)

if TESTING:
    logging.disable(logging.CRITICAL)

##############################################################################
# Fixup Settings and Defaults After Loading External Settings
##############################################################################

# Create base data directory.
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

for db in DATABASES.values():
    if db['ENGINE'] == 'django.db.backends.sqlite3':
        db_path = os.path.dirname(db['NAME'])
        if not os.path.exists(db_path):
            os.makedirs(db_path)

# Create directory for log files.
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Create directory for emails in development.
if EMAIL_FILE_PATH and not os.path.exists(EMAIL_FILE_PATH):
    os.makedirs(EMAIL_FILE_PATH)

# Make sure we initialize additional settings/variables if running under test.
if TESTING:
    from .__init__ import initialize
    initialize()
