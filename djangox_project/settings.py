import os
import environ
from django.contrib import messages
from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))
# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "43)%4yx)aa@a=+_c(fn&kf3g29xax+=+a&key9i=!98zyim=8j"

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    "*"
]
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "django.contrib.humanize",  # new
    "django.contrib.postgres",
    # Third-party
    "django_select2",
    "allauth",
    "allauth.account",  # new
    "crispy_forms",
    "crispy_bootstrap5",
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
    "product.middleware.RateMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "djangox_project.middleware.HtmxMessageMiddleware",
]

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
from django.utils.translation import gettext_lazy as _

LANGUAGES = (
    ("en", _("English")),
    ("fr", _("French")),
    ("hi", _("Hindi")),
)
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale/"),)
TIME_ZONE = "Asia/Kolkata"

# USE_I18N = True

USE_L10N = True
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

LOGIN_REDIRECT_URL = "dashboard"
ACCOUNT_LOGOUT_REDIRECT_URL = "account_login"

AUTHENTICATION_BACKENDS = (
    # 'graphql_jwt.backends.JSONWebTokenBackend',
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

SITE_ID = 1
ACCOUNT_ADAPTER = "invitations.models.InvitationsAdapter"

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
# CRISPY_FAIL_SILENTLY = not DEBUG

# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
#         'LOCATION': '127.0.0.1:11211',
#     }
# }
# CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_BROKER_URL = "amqp://localhost"
# CELERY_RESULT_BACKEND = "redis://localhost:6379"
CELERY_RESULT_BACKEND = "django-db"


MESSAGE_TAGS = {
    messages.DEBUG: "alert-info",
    messages.INFO: "alert-info",
    messages.SUCCESS: "alert-success",
    messages.WARNING: "alert-warning",
    messages.ERROR: "alert-danger",
}

PHONENUMBER_DEFAULT_REGION = "IN"
PHONENUMBER_DEFAULT_FORMAT = "NATIONAL"
MESSAGE_TAGS = {
    messages.DEBUG: "bg-light",
    messages.INFO: "text-white bg-primary",
    messages.SUCCESS: "text-white bg-success",
    messages.WARNING: "text-dark bg-warning",
    messages.ERROR: "text-white bg-danger",
}

TWILIO_ACCOUNT_SID = env("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = env("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = env("TWILIO_NUMBER")


SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
""" crontab() Execute every minute.
crontab(minute=0, hour=0) Execute daily at midnight.
crontab(minute=0, hour='*/3') Execute every three hours: midnight, 3am, 6am, 9am, noon, 3pm, 6pm, 9pm.
crontab(minute=0, hour='0,3,6,9,12,15,18,21') Same as previous.
crontab(minute='*/15') Execute every 15 minutes.
crontab(day_of_week='sunday') Execute every minute (!) at Sundays.
crontab(minute='*', hour='*', day_of_week='sun') Same as previous.
crontab(minute='*/10', hour='3,17,22', day_of_week='thu,fri') Execute every ten minutes, but only between 3-4 am, 5-6 pm, and 10-11 pm on Thursdays or Fridays.
crontab(minute=0, hour='*/2,*/3') Execute every even hour, and every hour divisible by three. This means: at every hour except: 1am, 5am, 7am, 11am, 1pm, 5pm, 7pm, 11pm
crontab(minute=0, hour='*/5') Execute hour divisible by 5. This means that it is triggered at 3pm, not 5pm (since 3pm equals the 24-hour clock value of “15”, which is divisible by 5).
crontab(minute=0, hour='*/3,8-17') Execute every hour divisible by 3, and every hour during office hours (8am-5pm).
crontab(0, 0, day_of_month='2') Execute on the second day of every month.
crontab(0, 0, day_of_month='2-30/2') Execute on every even numbered day.
crontab(0, 0, day_of_month='1-7,15-21') Execute on the first and third weeks of the month.
crontab(0, 0, day_of_month='11', month_of_year='5') Execute on the eleventh of May every year.
crontab(0, 0, month_of_year='*/3') Execute every day on the first month of every quarter.
"""
