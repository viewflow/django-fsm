PROJECT_APPS = ('django_fsm', 'testapp',)

INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'guardian',
) + PROJECT_APPS

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', # this is default
    'guardian.backends.ObjectPermissionBackend',
)

DATABASE_ENGINE = 'sqlite3'
SECRET_KEY = 'nokey'
MIDDLEWARE_CLASSES = ()
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
    }
}

ANONYMOUS_USER_ID = 0
