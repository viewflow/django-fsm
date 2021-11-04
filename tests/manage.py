# -*- coding: utf-8 -*-
import os
import sys
from django.core.management import execute_from_command_line

PROJECT_ROOT = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
sys.path.insert(0, PROJECT_ROOT)

if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv += ["test"]

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")
    execute_from_command_line(sys.argv)
