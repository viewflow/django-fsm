PROJECT_APPS = (
    'django_fsm',
    'testapp',
)
INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'guardian',
) + PROJECT_APPS
SECRET_KEY = 'nokey'
MIDDLEWARE_CLASSES = ()
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

ANONYMOUS_USER_ID = 0
