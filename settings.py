import os

DEBUG = TEMPLATE_DEBUG = True

BASE_DIR = os.path.abspath(os.path.dirname(__file__))  
PROJECT = BASE_DIR.split('/')[-1]

TIME_ZONE = 'America/Chicago'
LANGUAGE_CODE = 'en-us'

#SITE_ID = 1

USE_I18N = False
USE_L10N = False

STATIC_ROOT = os.path.join(BASE_DIR, 'static'),
STATIC_URL = '/static/'
#ADMIN_MEDIA_PREFIX = '/static/admin/'

SECRET_KEY = 'qj#hd!*j3+lfs3-(13t7f5ny+b*&3fgy)ej@6)h=5g4(%2g!g+'+PROJECT

ROOT_URLCONF = PROJECT+'.urls'

INSTALLED_APPS = (
    #'django.contrib.auth',
    #'django.contrib.contenttypes',
    #'django.contrib.sessions',
    #'django.contrib.sites',
    #'django.contrib.messages',
    'django.contrib.staticfiles',
    #'django.contrib.admin',
    PROJECT+'.website',
)