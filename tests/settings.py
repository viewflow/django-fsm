PROJECT_APPS = ('django_fsm',)
INSTALLED_APPS = ('django_hudson',) + PROJECT_APPS
DATABASE_ENGINE = 'sqlite3'

if __name__ == "__main__":
    import sys, test_runner as settings
    from django.core.management import execute_manager

    if len(sys.argv) == 1:
            sys.argv += ['test'] + list(PROJECT_APPS)
    execute_manager(settings)
