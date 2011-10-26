#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
from os import path
import shutil, sys, subprocess

PROJECT_ROOT = path.dirname(path.abspath(path.dirname(__file__)))
REQUIREMENTS = path.join(PROJECT_ROOT, 'tests', 'requirements.pip')

VE_ROOT = path.join(PROJECT_ROOT, '.ve')
VE_TIMESTAMP = path.join(VE_ROOT, 'timestamp')

envtime = path.exists(VE_ROOT) and path.getmtime(VE_ROOT) or 0
envreqs = path.exists(VE_TIMESTAMP) and path.getmtime(VE_TIMESTAMP) or 0
envspec = path.getmtime(REQUIREMENTS)


sys.path.insert(0, PROJECT_ROOT)

# run django
from django.core.management import execute_manager
try:
    import tests.settings
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv += ['test'] + list(tests.settings.PROJECT_APPS)
    execute_manager(tests.settings)
