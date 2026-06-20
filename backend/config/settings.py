"""
Django settings for config project.

Configuration is environment-driven. For local development the secure defaults
relax automatically (DEBUG on, secure cookies off). For production set
ENVIRONMENT=production and provide the secrets documented in `.env.template`.
"""

from pathlib import Path
import os
from datetime import timedelta

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


# --- small env helpers --------------------------------------------------------

def env_bool(key, default=False):
    return os.getenv(key, str(default)).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(key, default=''):
    return [item.strip() for item in os.getenv(key, default).split(',') if item.strip()]


ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')
IS_PRODUCTION = ENVIRONMENT == 'production'


# --- core ---------------------------------------------------------------------

# In production the secret MUST come from the environment. In development we fall
# back to an insecure, clearly-labelled key so the app runs out of the box.
SECRET_KEY = os.getenv(
    'DJANGO_SECRET_KEY',
    'django-insecure-dev-only-do-not-use-in-production',
)
if IS_PRODUCTION and SECRET_KEY.startswith('django-insecure'):
    raise RuntimeError("DJANGO_SECRET_KEY must be set in production.")

DEBUG = env_bool('DEBUG', default=not IS_PRODUCTION)

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS') or (
    ['localhost', '127.0.0.1', '[::1]'] if not IS_PRODUCTION else []
)
# Convenience: allow any *.vercel.app preview/prod host if requested.
if env_bool('ALLOW_VERCEL_HOSTS'):
    ALLOWED_HOSTS.append('.vercel.app')


# --- application definition ---------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'anymail',
    'api.apps.ApiConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# --- database -----------------------------------------------------------------
# Uses DATABASE_URL when present (required for serverless/Vercel — SQLite cannot
# persist on an ephemeral filesystem), otherwise falls back to local SQLite.

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=IS_PRODUCTION and bool(os.getenv('DATABASE_URL')),
    )
}


# --- password validation ------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# --- i18n ---------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# --- static files (WhiteNoise) ------------------------------------------------

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': (
            'whitenoise.storage.CompressedManifestStaticFilesStorage'
            if IS_PRODUCTION
            else 'django.contrib.staticfiles.storage.StaticFilesStorage'
        ),
    },
}

AUTH_USER_MODEL = 'api.User'


# --- Django REST Framework ----------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        # Browser SPA uses httpOnly cookies (CSRF-protected); header auth is a
        # fallback for non-browser API clients.
        'api.authentication.CookieJWTAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Deny writes by default; public read endpoints opt in explicitly.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_THROTTLE_CLASSES': (
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'anon': os.getenv('THROTTLE_ANON', '60/min'),
        'user': os.getenv('THROTTLE_USER', '600/min'),
        'login': os.getenv('THROTTLE_LOGIN', '10/min'),
        'submit': os.getenv('THROTTLE_SUBMIT', '20/hour'),
    },
    'DEFAULT_RENDERER_CLASSES': (
        ('rest_framework.renderers.JSONRenderer',)
        if IS_PRODUCTION
        else (
            'rest_framework.renderers.JSONRenderer',
            'rest_framework.renderers.BrowsableAPIRenderer',
        )
    ),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.getenv('ACCESS_TOKEN_MINUTES', '15'))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('REFRESH_TOKEN_DAYS', '7'))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}


# --- auth cookies (consumed by api.authentication / auth views) ---------------

AUTH_COOKIE = 'access_token'
AUTH_REFRESH_COOKIE = 'refresh_token'
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_SECURE = IS_PRODUCTION
AUTH_COOKIE_SAMESITE = os.getenv('AUTH_COOKIE_SAMESITE', 'Lax')
AUTH_COOKIE_PATH = '/'


# --- CORS / CSRF --------------------------------------------------------------
# Preferred deployment keeps the API same-origin via a Vercel rewrite / Vite
# proxy, so CORS is mostly belt-and-braces. Never allow all origins.

CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS') or (
    ['http://localhost:5173', 'http://127.0.0.1:5173'] if not IS_PRODUCTION else []
)
CORS_ALLOW_CREDENTIALS = True

CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS') or (
    ['http://localhost:5173', 'http://127.0.0.1:5173'] if not IS_PRODUCTION else []
)

CSRF_COOKIE_HTTPONLY = False   # the SPA must read it to echo X-CSRFToken
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_HTTPONLY = True


# --- production-only security hardening ---------------------------------------

if IS_PRODUCTION:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    X_FRAME_OPTIONS = 'DENY'


# --- email --------------------------------------------------------------------

if IS_PRODUCTION:
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    ANYMAIL = {
        "MAILGUN_API_KEY": os.getenv('MAILGUN_API_KEY'),
        "MAILGUN_SENDER_DOMAIN": os.getenv('MAILGUN_SENDER_DOMAIN'),
    }
    DEFAULT_FROM_EMAIL = f"noreply@{os.getenv('MAILGUN_SENDER_DOMAIN')}"
else:
    EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
    EMAIL_FILE_PATH = BASE_DIR / "sent_emails"
    DEFAULT_FROM_EMAIL = "testing@example.com"
