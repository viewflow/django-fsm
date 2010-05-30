#!/bin/bash -e
SCRIPT_DIR=`dirname $0`
DEST_DIR=`mktemp -t -d ci-django-fsm-XXX`

cd $SCRIPT_DIR

# Setup environment
virtualenv --no-site-packages $DEST_DIR
source $DEST_DIR/bin/activate

pip install -r environment.pip

# Run tests
python <<EOF
from django import conf
from django.core import management

__name__ = 'django_fsm.tests'
class TestSettings(conf.UserSettingsHolder):
   INSTALLED_APPS=('django_fsm',)
   DATABASE_ENGINE='sqlite3'
   TEST_RUNNER = 'django_nose.run_tests'
   NOSE_ARGS = ['django_fsm',
                '--with-coverage',
                '--cover-package=django_fsm',
                '--with-xunit',
                '--with-xcoverage']

conf.settings.configure(TestSettings(conf.global_settings))
management.call_command('test')
EOF
