PROJECT_APPS = ('django_fsm', 'testapp',)
INSTALLED_APPS = ('django_jenkins',) + PROJECT_APPS
DATABASE_ENGINE = 'sqlite3'
SECRET_KEY = 'nokey'

DATABASE_ENGINE = 'sqlite3'
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.%s' % DATABASE_ENGINE,
        }
}

if __name__ == "__main__":
    import sys, test_runner as settings
    from django.core.management import execute_manager

    if len(sys.argv) == 1:
            sys.argv += ['test'] + list(PROJECT_APPS)
    execute_manager(settings)
