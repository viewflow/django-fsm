#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
from os import path
import shutil, sys, virtualenv, subprocess

PROJECT_ROOT = path.dirname(path.abspath(path.dirname(__file__)))
REQUIREMENTS = path.join(PROJECT_ROOT, 'tests', 'requirements.pip')

VE_ROOT = path.join(PROJECT_ROOT, '.ve')
VE_TIMESTAMP = path.join(VE_ROOT, 'timestamp')

envtime = path.exists(VE_ROOT) and path.getmtime(VE_ROOT) or 0
envreqs = path.exists(VE_TIMESTAMP) and path.getmtime(VE_TIMESTAMP) or 0
envspec = path.getmtime(REQUIREMENTS)

def go_to_ve():
    # going into ve
    if not sys.prefix == VE_ROOT:
        if sys.platform == 'win32':
            python = path.join(VE_ROOT, 'Scripts', 'python.exe')
        else:
            python = path.join(VE_ROOT, 'bin', 'python')
            
        retcode = subprocess.call([python, __file__] + sys.argv[1:])
        sys.exit(retcode)

update_ve = 'update_ve' in sys.argv
if update_ve or envtime < envspec or envreqs < envspec:
    if update_ve:
        # install ve
        if envtime < envspec:
            if path.exists(VE_ROOT):
                shutil.rmtree(VE_ROOT)
            virtualenv.logger = virtualenv.Logger(consumers=[])
            virtualenv.create_environment(VE_ROOT, site_packages=True)

        go_to_ve()    

        # check requirements
        if update_ve or envreqs < envspec:
            import pip
            pip.main(initial_args=['install', '-r', REQUIREMENTS])
            file(VE_TIMESTAMP, 'w').close()
        sys.exit(0)
    else:
        print "VirtualEnv need to be updated"
        print "Run ./manage.py update_ve"
        sys.exit(1)

go_to_ve()

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
