# Python
import os
import threading
import sys

_initialized = threading.Event()


def initialize():
    if _initialized.is_set():
        return
    _initialized.set()

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'test_project.settings')


def main(*args):
    initialize()
    from django.core.management import execute_from_command_line
    execute_from_command_line(args or sys.argv)
