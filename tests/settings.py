PROJECT_APPS = ('django_fsm', 'testapp',)
INSTALLED_APPS = ('django.contrib.contenttypes', 'django.contrib.auth', 'django_jenkins',) + PROJECT_APPS
DATABASE_ENGINE = 'sqlite3'
SECRET_KEY = 'nokey'
MIDDLEWARE_CLASSES = ()
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        }
}

JENKINS_TASKS = (
    'django_jenkins.tasks.with_coverage',
    'django_jenkins.tasks.run_pep8',
    'django_jenkins.tasks.run_pyflakes'
)
