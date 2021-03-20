# Celery
from celery import shared_task

# Celery-Task-Plus
from celery_task_plus.tasks import LockedTask, DirectResultsTask, LockedDirectResultsTask


@shared_task(
    name='test_app.normal_task',
)
def normal_task():
    pass


@shared_task(
    name='test_app.locked_task',
    base=LockedTask,
)
def locked_task():
    pass


@shared_task(
    name='test_app.direct_results_task',
    base=DirectResultsTask,
)
def direct_results_task():
    pass


@shared_task(
    name='test_app.locked_direct_results_task',
    base=LockedDirectResultsTask,
)
def locked_direct_results_task():
    pass
