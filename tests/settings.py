import django

PROJECT_APPS = (
    "django_fsm",
    "testapp",
)

INSTALLED_APPS = (
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "guardian",
) + PROJECT_APPS

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",  # this is default
    "guardian.backends.ObjectPermissionBackend",
)

DATABASE_ENGINE = "sqlite3"
SECRET_KEY = "nokey"
MIDDLEWARE_CLASSES = ()
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
    }
}

if django.VERSION < (1, 9):

    class DisableMigrations(object):
        def __contains__(self, item):
            return True

        def __getitem__(self, item):
            return "notmigrations"

    MIGRATION_MODULES = DisableMigrations()
else:
    MIGRATION_MODULES = {
        "auth": None,
        "contenttypes": None,
        "guardian": None,
    }


ANONYMOUS_USER_ID = 0

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
