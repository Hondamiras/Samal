import os
from decouple import config
from pathlib import Path
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = [
    "samaltp.kz",
    "www.samaltp.kz",
    "samaltrading.kz",
    "www.samaltrading.kz",
]

CSRF_TRUSTED_ORIGINS = [
    "https://samaltp.kz",
    "https://www.samaltp.kz",
    "https://samaltrading.kz",
    "https://www.samaltrading.kz",
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'whitenoise.runserver_nostatic',  # Добавляем Whitenoise
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    #my apps
    'samal.apps.SamalConfig',

    #third party apps
    'smart_selects',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Добавляем Whitenoise
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASS'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

# import dj_database_url

# DATABASES = {
#     'default': dj_database_url.config(default="sqlite:///db.sqlite3")
# }



# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = '/static/'

# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Если вы используете реальный SMTP-сервер:
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# EMAIL_HOST_USER = "khondamiras@gmail.com"   # логин для SMTP-сервера
EMAIL_HOST_PASSWORD = "zmvf lnky jpyk usbu"           # пароль для SMTP-сервера

# # Адрес, с которого будут отправляться письма
# DEFAULT_FROM_EMAIL = "khondamiras@gmail.com"

# Адрес получателя сообщений с сайта (например, для обратной связи)
CONTACT_EMAIL = 'khondamiras@gmail.com'
ORDER_EMAIL = 'khondamiras@gmail.com'


# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# settings.py
EMAIL_HOST         = "smtp-relay.brevo.com"
EMAIL_PORT         = 2525          # открыт у DigitalOcean
EMAIL_USE_TLS      = True
EMAIL_HOST_USER    = "8c290c001@smtp-brevo.com"
EMAIL_HOST_PASSWORD = "FWVhTZX5cxjq0f6N"
DEFAULT_FROM_EMAIL = "khondamiras@gmail.com"
EMAIL_TIMEOUT      = 10            # чтобы воркер не зависал
