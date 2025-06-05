from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.redis import RedisJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

import os
import redis
import telebot
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
PAY_SECRET = os.getenv('PAY_SECRET')

DEBUG = os.getenv('DEBUG')

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))

REDIS_CLIENT = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0)


if DEBUG:
    ALLOWED_HOSTS = ['*']
    BOT_TOKEN = os.getenv('TEST_TOKEN')
    GOOGLE_KEY_PATH = os.path.join('data', 'cred.json')

else:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'nginx', '89.111.155.92']
    BOT_TOKEN = os.getenv('TOKEN')
    GOOGLE_KEY_PATH = os.path.join('data', 'cred.json')

bot = telebot.TeleBot(BOT_TOKEN, parse_mode='html')


# Настройка планировщика
jobstores = {
    'default': RedisJobStore(host=REDIS_HOST, port=REDIS_PORT, db=1)
}
executors = {
    'default': ThreadPoolExecutor(10)
}
job_defaults = {
    'coalesce': True,
    'max_instances': 3
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
scheduler.start()


# Application definition
INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'bot_admin',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'web.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'web.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

jobstores = {
    'default': RedisJobStore(host=REDIS_HOST, port=REDIS_PORT, db=1)
}
executors = {
    'default': ThreadPoolExecutor(10)
}
job_defaults = {
    'coalesce': True,
    'max_instances': 3
}

scheduler = BackgroundScheduler(jobstores=jobstores, executors=executors, job_defaults=job_defaults)
scheduler.start()

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


LANGUAGE_CODE = 'ru-ru'

LOCAL_TZ = ZoneInfo('Asia/Tashkent')

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

DATE_FORMAT = '%d.%m.%Y'
TIME_SHORT_FORMAT = '%H:%M'
DATETIME_FORMAT = '%H:%M %d.%m.%Y'
DATETIME_FORMAT_ISO = '%Y-%m-%dT%H:%M:%SZ'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STATIC_URL = '/static/'

STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

LOG_DIR = os.path.join(BASE_DIR, 'logs')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'when': 'midnight',
            'backupCount': 7,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            # 'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },

        'view_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': os.path.join(LOG_DIR, 'view.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },

        'view_logger': {
            'handlers': ['view_file'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# import os
#
# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': False,
#
#     'formatters': {
#         'verbose': {
#             'format': '[{asctime}] [{levelname}] [{name}] {message}',
#             'style': '{',
#         },
#     },
#
#     'handlers': {
#         'view_file': {
#             'level': 'INFO',
#             'class': 'logging.FileHandler',
#             'filename': os.path.join(BASE_DIR, 'logs', 'view.log'),
#             'formatter': 'verbose',
#         },
#     },
#
#     'loggers': {
#         'view_logger': {
#             'handlers': ['view_file'],
#             'level': 'INFO',
#             'propagate': False,
#         },
#     }
# }
