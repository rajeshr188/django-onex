import os

import environ
from django.contrib import messages
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
environ.Env.read_env()
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "43)%4yx)aa@a=+_c(fn&kf3g29xax+=+a&key9i=!98zyim=8j"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "*",
    "192.168.1.100",
    "192.168.1.101",
    "192.168.102",
    "localhost",
    "127.0.0.1",
]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
# Application definition

INSTALLED_APPS = [
    "django_select2",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",  # new
    # Third-party
    "allauth",
    "allauth.account",  # new
    "crispy_forms",
    "crispy_bootstrap5",
    "import_export",
    "versatileimagefield",  # new
    "rest_framework",
    "mptt",
    "phonenumber_field",
    "django_tables2",
    "django_filters",
    "djmoney",
    "widget_tweaks",
    "debug_toolbar",
    "django_extensions",
    "django_htmx",
    "django_celery_beat",
    "django_celery_results",
    # Local
    "users",
    "pages",
    "contact",
    "product",
    "girvi",
    "invoice",
    "sales",
    "purchase",
    "approval",
    "Chitfund",
    "daybook",
    "dea",
    "sea",
    "notify",
]

MIDDLEWARE = [
    # 'django.middleware.cache.UpdateCacheMiddleware',
    # 'django.middleware.cache.FetchFromCacheMiddleware',
    "django_htmx.middleware.HtmxMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "djangox_project.middleware.HtmxMessageMiddleware",
]
REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    "DEFAULT_PERMISSION_CLASSES": [
        # 'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly',
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    # 'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    # 'PAGE_SIZE': 10
}
# CACHE_MIDDLEWARE_ALIAS = 'default'
# CACHE_MIDDLEWARE_SECONDS = 604800
# CACHE_MIDDLEWARE_KEY_PREFIX = 'jsk'

ROOT_URLCONF = "djangox_project.urls"
INTERNAL_IPS = ["127.0.0.1", "localhost"]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "djangox_project.wsgi.application"


# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "onex",
        "USER": "postgres",
        "PASSWORD": "kanchan",
        "HOST": "localhost",
        "PORT": "5432",
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

# USE_I18N = True

# USE_L10N = True
SHORT_DATETIME_FORMAT = "d-m-Y"
DATETIME_INPUT_FORMATS = [
    "%d/%m/%Y %I:%M %p",
]
USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.1/howto/static-files/
STATIC_ROOT = os.path.join("staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

AUTH_USER_MODEL = "users.CustomUser"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGIN_REDIRECT_URL = "home"
ACCOUNT_LOGOUT_REDIRECT_URL = "home"

AUTHENTICATION_BACKENDS = (
    # 'graphql_jwt.backends.JSONWebTokenBackend',
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

SITE_ID = 1


ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = False
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_AUTHENTICATION_METHOD = "email"
ACCOUNT_UNIQUE_EMAIL = True

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

CRISPY_TEMPLATE_PACK = "bootstrap5"
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"


# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#         'LOCATION': '127.0.0.1:11211',
#     }
# }
CELERY_BROKER_URL = "redis://localhost:6379"
# CELERY_BROKER_URL = 'amqp://localhost'
CELERY_RESULT_BACKEND = "redis://localhost:6379"
# CELERY_RESULT_BACKEND = 'django-db'

CELERY_BEAT_SCHEDULE = {
    "scheduled_task": {
        "task": "contact.tasks.add",
        "schedule": 5.0,
        "args": (10, 10),
    },
}

MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

PHONENUMBER_DEFAULT_REGION = "IN"


MESSAGE_TAGS = {
    messages.DEBUG: "bg-light",
    messages.INFO: "text-white bg-primary",
    messages.SUCCESS: "text-white bg-success",
    messages.WARNING: "text-dark bg-warning",
    messages.ERROR: "text-white bg-danger",
}
