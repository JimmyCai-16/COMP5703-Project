"""
Django settings for main project.

Generated by 'django-admin startproject' using Django 4.2.dev20230116083134.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

## For adding GDAL to the environment, check README for explanation
if os.name == 'nt':
    VENV_BASE = os.environ['VIRTUAL_ENV']
    os.environ['PATH'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo') + ';' + os.environ['PATH']
    os.environ['PROJ_LIB'] = os.path.join(VENV_BASE, 'Lib\\site-packages\\osgeo\\data\\proj') + ';' + os.environ['PATH']

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-^#f@e(-h%=$vdha5x)j9n44^n0sl2)92sav8eknl&@_g9tu2tk')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

CORS_ALLOW_HEADERS = (
    'x-requested-with',
    'content-type',
    'accept',
    'origin',
    'authorization',
    'accept-encoding',
    'x-csrftoken',
    'access-control-allow-origin',
    'content-disposition',
    'withcredentials',
    'cookie',
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS')
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000',  # Example: Allow requests from your frontend application running on localhost
    "http://127.0.0.1:3000" 
       # Add more origins as needed
]
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
SITE_HOST = "127.0.0.1"
SITE_ID = 1
SITE_URL = 'http://127.0.0.1:8000'


# Application definition
PROJECT_APPS = [
    'object_permissions',
    'forms',
    'user',
    'website',
    'data_catalogue',
    'appboard',
    'media_file',
    'project',
    'tms',
    'lms',
    'native_title_management',
    'geochem',
    'interactive_map',
    'geodesk_gis',
    'project_management',
    'autoform',
    'knowledge_management_system',
    'notification',
    'porphyry_deposits'
]


INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'daphne',
    'attrs',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    "django.contrib.gis",
    "django.contrib.sites",
    'django.contrib.humanize',
    'leaflet',

    'channels',
    'common',
] + PROJECT_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'main.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.template.context_processors.request',
                'django.contrib.messages.context_processors.messages',
                'djconfig.context_processors.config',
                'appboard.contextprocessors.create_project_form',
            ],
        },
    },
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
     ),
     'DEFAULT_PERMISSIONS_CLASSES': (
      'rest_framework.permissions.IsAuthenticated',
        'rest_framework.permissions.IsAdminUser',
         
     ),
}

#Authentication backends
AUTHENTICATION_BACKENDS = (
    #'user.authentication.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

WSGI_APPLICATION = 'main.wsgi.application'
ASGI_APPLICATION = 'main.asgi.application'

# TODO: In production we want to use a redis server.
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

# Database
# https://docs.djangoproject.com/en/dev/ref/settings/#databases

# Just basic setups for different backends, our .env file will define which is actually used as shown below
# this definition. Defaults to sqlite3.
_db_backend_options = {
    'MYSQL': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    },
    'POSTGRES': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
    'POSTGIS': {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    },
    'sqlite3': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DATABASES = {
    'default': {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASS'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }  # _db_backend_options[os.environ.get('DB_BACKEND', 'sqlite3')]
}

# Password validation
# https://docs.djangoproject.com/en/dev/ref/settings/#auth-password-validators

AUTH_USER_MODEL = 'user.User'
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'  # 'mandatory' #'optional' 'none'

# Email confirmation
ACCOUNT_EMAIL_SUBJECT_PREFIX = "[OreFox.com]"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True

# After 10 failed login attempts, restrict logins for 30 minutes
ACCOUNT_LOGIN_ATTEMPTS_LIMIT = 5
ACCOUNT_LOGIN_ATTEMPTS_TIMEOUT = 1800
ACCOUNT_PASSWORD_MIN_LENGTH = 8

# Other settings
# ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
ACCOUNT_LOGIN_ON_PASSWORD_RESET = True
SOCIALACCOUNT_AUTO_SIGNUP = False

LOGIN_REDIRECT_URL = 'appboard:home'
ACCOUNT_LOGOUT_REDIRECT_URL = 'user:login'


# Internationalization
# https://docs.djangoproject.com/en/dev/topics/i18n/

LANGUAGE_CODE = 'en-AU'
TIME_ZONE = 'Australia/Brisbane'
DATE_FORMAT = 'M, d. Y'
DATETIME_FORMAT = 'M, d. Y. H:i:s e'
USE_I18N = True
USE_L10N = False

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/dev/howto/static-files/

STATIC_ROOT = os.path.join(BASE_DIR, 'static_root', 'static')
STATIC_URL = 'static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media_root', 'media')
MEDIA_URL = 'media/'

# Default primary key field type
# https://docs.djangoproject.com/en/dev/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(BASE_DIR, 'st_search'),
    },
}
HAYSTACK_SIGNAL_PROCESSOR = 'spirit.search.signals.RealtimeSignalProcessor'

ST_SITE_URL = 'http://127.0.0.1:8000/'

LOGIN_URL = 'user:login'
LOGIN_REDIRECT_URL = 'appboard:home'
LOGOUT_REDIRECT_URL = 'user:login'

#Password_reset

EMAIL_BACKEND= 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER= 'testbot.orefox@gmail.com'
EMAIL_HOST_PASSWORD= 'dmfuabickxfkkljk'

PASSWORD_RESET_TIMEOUT = 1440

#haoran STRIPE_SECRET_KEY="sk_test_51NccGMJ3jZ6WQD1W0ltgAPvb2wUt1mrKJh1OyIYWV5uVmDLNfGvRnyDPzmPeM9J7KP6aCEhPtre4lMZjLLBtLfvJ00mi3RXwfy"
STRIPE_SECRET_KEY="sk_test_51NLeF1E5nog93nDG5Ju0wA6IuNv80XhvM6VR53fEkei33hHzh4w1yuO7SG7ExQk1RhXs9329xLYVPWxyrNAgC19h00vc4xmciL"
#STRIPE_SECRET_KEY = "pk_test_51NLeF1E5nog93nDGfVv6nCUpuHSI88NCFxse4piZtboICuARzm4AqMnmtg9lrlT7LO1cGoUdkw2SA6g7bnJZQS93009NdjCdZ1"
# haoran STRIPE_SECRET_WEBHOOK = "whsec_e6b504f7e9005844a06b8e67b5d718b3defa224464d8ef9fc72e4cb3f04472d3"
STRIPE_SECRET_WEBHOOK="whsec_1ff749461c976c657ead08e10426c307f1fdac8742133e8f8eed16a4a0f3a4ce"

#APPSTORE URLs
APP_STORE_URL="http://127.0.0.1:3000"
APP_STORE_FRONTEND_URL='"http://127.0.0.1:3000"/home'
FRONTEND_DOMAIN = "http://127.0.0.1:3000"
# handler404 = 'main.urls.page_not_found_view'

# # For mac user installing GDAL 
GDAL_LIBRARY_PATH = '/opt/homebrew/Cellar/gdal/3.9.1_1/lib/libgdal.35.dylib' 
GEOS_LIBRARY_PATH = '/opt/homebrew/Cellar/geos/3.12.2/lib/libgeos_c.1.dylib'
