import sys
from os import path

PROJECT_ROOT = path.dirname(path.abspath(path.dirname(__file__)))
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
