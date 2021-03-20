# Python
import contextlib
import json
import logging
import os
import socket
import urllib.parse
import uuid

# Django
from django.conf import settings
from django.core.cache import cache
from django.utils.text import slugify

# Celery
from celery import states, Task
from celery.app.task import Context
from celery.exceptions import Ignore, Reject

# Redis
from redis import StrictRedis

# Python-Redis-Lock
import redis_lock

logger = logging.getLogger('celery_task_plus.tasks')

__all__ = ['LockedTask', 'DirectResultsTask', 'LockedDirectResultsTask']


class LockedTask(Task):

    abstract = True

    # Include name in task key? True or <str>
    task_key_name = True
    # Include args in task_key? True or <int> (for number of positional args).
    task_key_args = True
    # Include kwargs in task_key? True or iterable of keys to include.
    task_key_kwargs = True
    # If None, task will block until lock is released. If 0, task will fail immediately if lock cannot be acuired.
    # If > 0, task will wait up to this many seconds to acquire the lock.
    task_lock_timeout = 0

    @classmethod
    def _get_task_key(cls, *args, **kwargs):
        if cls.task_key_name is True:
            task_key_name = cls.name
        else:
            task_key_name = '{}'.format(cls.task_key_name or '')
        task_key_args = []
        if cls.task_key_args is True:
            task_key_args.extend([json.dumps(a) for a in args[:]])
        elif isinstance(cls.task_key_args, int):
            task_key_args.extend([json.dumps(a) for a in args[:cls.task_key_args]])
        if cls.task_key_kwargs:
            for k in sorted(kwargs.keys()):
                if cls.task_key_kwargs is True or k in cls.task_key_kwargs:
                    task_key_args.append('{}={}'.format(k, json.dumps(kwargs[k])))
        if task_key_args:
            task_key = '{}-{}'.format(task_key_name, '-'.join(task_key_args))
        else:
            task_key = task_key_name
        task_key = task_key.replace('.', '-').replace('_', '-')
        return slugify(task_key)[:250]

    @classmethod
    def _get_owner_id(cls):
        return urllib.parse.urlencode([
            ('hostname', socket.gethostname()),
            ('pid', os.getpid()),
        ]).encode('utf-8')

    @classmethod
    def _get_redis_lock(cls, task_key, expire=60, auto_renewal=True):
        try:
            redis_client = cache.client.get_client()
        except AttributeError:
            redis_client = StrictRedis.from_url(settings.REDIS_URL)
        owner_id = cls._get_owner_id()
        return redis_lock.Lock(redis_client, task_key, id=owner_id, expire=expire, auto_renewal=auto_renewal)

    @classmethod
    @contextlib.contextmanager
    def _lock_task(cls, task_key, exc_class=Reject):
        if cls.task_lock_timeout is None:
            expire = 60
            blocking = True
            timeout = None
        elif cls.task_lock_timeout == 0:
            expire = 60
            blocking = False
            timeout = None
        else:
            expire = max(60, cls.task_lock_timeout)
            blocking = True
            timeout = cls.task_lock_timeout
        owner_id = cls._get_owner_id()
        lock = cls._get_redis_lock(task_key, expire)
        acquired = False
        try:
            if blocking:
                timeout_display = '{}s'.format(timeout) if timeout else 'indefinitely'
                logger.debug('Waiting {0} for lock: {1}'.format(timeout_display, task_key))
            acquired = lock.acquire(blocking=blocking, timeout=timeout)
            if acquired:
                logger.debug('Acquired the lock: {0} @ {1}'.format(task_key, owner_id))
                yield
            else:
                if lock.get_owner_id() == owner_id:
                    msg = 'Already acquired this lock: {0} @ {1}'.format(task_key, owner_id)
                else:
                    msg = 'Lock held by another process: {0} @ {1}'.format(task_key, lock.get_owner_id())
                logger.debug(msg)
                raise exc_class(msg)
        finally:
            if acquired:
                lock.release()
                logger.debug('Released the lock: {0} @ {1}'.format(task_key, owner_id))

    def __call__(self, *args, **kwargs):
        with self._lock_task(self._get_task_key(*args, **kwargs)):
            return super().__call__(*args, **kwargs)


class DirectResultsTask(Task):

    abstract = True

    def __call__(self, *args, **kwargs):
        task_id = self.request.id or uuid.uuid4()
        task_result = None
        task_exc = None

        # Determine if task is called outside of a worker (via apply or
        # __call__).
        task_is_direct = self.request.is_eager or self.request.called_directly

        # If called directly via __call__, create a placeholder request context
        # used for the result backend.
        if self.request.called_directly:
            task_request = Context({}, task=self.name, args=args, kwargs=kwargs)
        else:
            task_request = self.request

        # Celery already tracks the started state from the worker when:
        #   (track_started and not eager and not ignore_result)
        # Set a flag to store started status for eager or direct calls.
        store_started = task_is_direct and self.track_started and not self.ignore_result

        # Celery already stores task results from the worker when:
        #   (not eager and not ignore_result)
        # Set flags to store results, errors and ignored exceptions for eager or
        # direct calls.
        store_result = task_is_direct and not self.ignore_result
        store_errors = task_is_direct and (not self.ignore_result or self.store_errors_even_if_ignored)
        store_ignored = not self.ignore_result or self.store_errors_even_if_ignored
        store_revoked = not self.ignore_result or self.store_errors_even_if_ignored

        # Store started state for eager or direct tasks.
        if store_started:
            meta = dict(pid=os.getpid(), hostname=socket.gethostname())
            self.backend.store_result(task_id, meta, states.STARTED, request=task_request)
            logger.debug('Marked task_id = {} as started'.format(task_id))

        try:
            # Run the actual task.
            task_result = super().__call__(*args, **kwargs)
            return task_result
        except (Ignore, Reject) as e:
            task_exc = e
            raise
        except Exception as e:
            task_exc = e
            raise
        finally:
            if task_exc:
                # Store ignored state for any tasks (since worker does not store
                # this state).
                if isinstance(task_exc, Ignore):
                    if store_ignored:
                        self.backend.store_result(task_id, str(task_exc), states.IGNORED, request=task_request)
                        logger.debug('Marked task_id = {0} as ignored: {1!r}'.format(task_id, task_exc))
                        # FIXME: Send event!
                # Store rejected/revoked state for any tasks (since worker does
                # not store this state as a result of a Reject exception).
                elif isinstance(task_exc, Reject):
                    if store_revoked:
                        if not task_is_direct:
                            self.send_event('task-rejected', requeue=False)
                        self.backend.mark_as_revoked(task_id, task_exc, request=task_request)
                        logger.debug('Marked task_id = {0} as revoked: {1!r}'.format(task_id, task_exc))
                # Store errors for eager or direct tasks.
                elif store_errors:
                    self.backend.mark_as_failure(task_id, task_exc, request=task_request)
                    logger.debug('Marked task_id = {0} as failure: %{1!r}'.format(task_id, task_exc))
            # Store results for eager or direct tasks.
            elif store_result:
                self.backend.mark_as_done(task_id, task_result, request=task_request)
                logger.debug('Marked task_id = {0} as done: {1!r}'.format(task_id, task_exc))


class LockedDirectResultsTask(DirectResultsTask, LockedTask):

    abstract = True
