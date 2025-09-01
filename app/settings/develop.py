import os
from .common import *


DEBUG = True

SECRET_KEY = 'django-insecure-ah(qcb796w3v@=_0(+4dx!a2a862hed6)--0cgjyx%x*oc07(l'


if DEBUG:
    DEBUG_TOOLBAR_MIDDLEWARE = "debug_toolbar.middleware.DebugToolbarMiddleware"
    MIDDLEWARE.insert(0, DEBUG_TOOLBAR_MIDDLEWARE)


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'scheduler_db',
        'USER': 'postgres',
        'PASSWORD': 'par3948s',
        'HOST': 'localhost',
        'PORT': '5432'
    }
}