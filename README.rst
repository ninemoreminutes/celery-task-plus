|PyPI Version| |PyPI License| |Python Versions| |Django Versions|

Celery-Task-Plus
================

Celery-Task-Plus is a work-in-progress providing a few small enhancements to Celery.
More documentation and tests to come!

LockedTask
----------

``celery_task_plus.tasks.LockedTask`` is an abstract base class for tasks to prevent
multiple instances of the same task from running based on task name or a unique
identifier, positional arguments, or keyword arguments.

DirectResultsTask
-----------------

``celery_task_plus.tasks.DirectResultsTask`` is an abstract base class to store task
results when tasks are started outside of a worker.


.. |PyPI Version| image:: https://img.shields.io/pypi/v/celery-task-plus.svg
   :target: https://pypi.python.org/pypi/celery-task-plus/
.. |PyPI License| image:: https://img.shields.io/pypi/l/celery-task-plus.svg
   :target: https://pypi.python.org/pypi/celery-task-plus/
.. |Python Versions| image:: https://img.shields.io/pypi/pyversions/celery-task-plus.svg
   :target: https://pypi.python.org/pypi/celery-task-plus/
.. |Django Versions| image:: https://img.shields.io/pypi/djversions/celery-task-plus.svg
   :target: https://pypi.org/project/celery-task-plus/
