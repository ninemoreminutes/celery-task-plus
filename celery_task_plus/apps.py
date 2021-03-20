# Django
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CeleryTaskPlusConfig(AppConfig):

    name = 'celery_task_plus'
    verbose_name = _('Celery Task Plus')

    def ready(self):
        from .patches import patch_django_celery_results
        patch_django_celery_results()
