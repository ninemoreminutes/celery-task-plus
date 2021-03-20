# Celery
from celery import Celery

# Django
from django.apps import apps

# Test Project
from . import initialize

# This module will be loaded by either:
# - celery -A test_project <command>
# - manage.py <command> via test_project.test_app.apps:TestAppConfig.ready()

initialize()

# Create default Celery app for project.
app = Celery('test_project')

# Configure Celery from Django settings prefixed with CELERY_.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(force=bool(apps.ready))
