"""
Django settings for untitled project.

Generated by 'django-admin startproject' using Django 2.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'vixpmpn41mc-fq9#wyf)qs52)jt$rs$=%i=ens(+d*ch)ccz!d'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [
    '202.207.178.209',
]

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'monitor',
    'qos',
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

ROOT_URLCONF = 'untitled.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'untitled.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Redis连接
REDIS_CONN = {
    'HOST': '192.168.198.128',
    'PORT': 6379,
    'PASSWD': '123456'
}

# 订阅频道
TRIGGER_CHAN = 'trigger_event_channel'

# 数据优化参数
STATUS_DATA_OPTIMIZATION = {
    'latest': [0, 600],  # 0 存储真实数据,600个点
    '10mins': [600, 2016],  # 两周内：每10分钟存一个记录点，10分钟内的数据取平均值，一共有2016个记录点
    '20mins': [1200, 2160],  # 一个月内：每20分钟存一个记录点，20分钟内的数据取平均值，一共有2160个记录点
    '60mins': [3600, 4320],  # 半年内：每60分钟存一个记录点，60分钟内的数据取平均值，一共有4320个记录点
    '2hours': [7200, 4380],  # 一年内：每2小时存一个记录点，2小时内的数据取平均值，一共有4380个记录点
    '6hours': [21600, 2920],  # 两年内：每6小时存一个记录点，6小时内的数据取平均值，一共有2920个记录点
    '1day': [86400, 1825],  # 五年内：每24小时存一个记录点，24小时内的数据取平均值，一共有1825个记录点
    '3day': [259200, 1220],  # 十年内：每3天存一个记录点，3天内的数据取平均值，一共有1220个记录点
}

# 允许服务报告晚于监视时间间隔不超过规定的秒
REPORT_LATE_TOLERANCE_TIME = 10

# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Shanghai'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (
            os.path.join(BASE_DIR, 'static'),
    )


IP_DB_FILE = "%s/qos/backends/src/ipdb-20140902-99884.txt" % BASE_DIR

REPORT_ITEMS = ('firstPaint', 'domReadyTime', 'lookupDomainTime',
                'requestTime', 'loadTime', 'redirectTime',
                )


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
ACCOUNT_ACTIVATION_DAYS = 7
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
# EMAIL_HOST = 'smtp.163.com'
EMAIL_HOST = 'smtp.qq.com'
EMAIL_PORT = 465
# EMAIL_HOST_USER = 'cq146637@163.com'
EMAIL_HOST_USER = '1016025625@qq.com'
# EMAIL_HOST_PASSWORD = 'qwqw1560'
EMAIL_HOST_PASSWORD = 'wtjthxuryuoibeaj'
DEFAULT_FROM_EMAIL = 'CQ<1016025625@qq.com>'
# DEFAULT_FROM_EMAIL = 'CQ<cq146637@163.com>'
