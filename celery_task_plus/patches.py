# Python
import threading

_django_celery_results_patched = threading.Event()


def patch_django_celery_results():
    if _django_celery_results_patched.is_set():
        return
    _django_celery_results_patched.set()

    # Patch TaskResultsAdmin to prevent add/change.
    from django_celery_results.admin import TaskResultAdmin

    def has_add_permission(self, request):
        return False

    TaskResultAdmin.has_add_permission = has_add_permission

    def has_change_permission(self, request, obj=None):
        return False

    TaskResultAdmin.has_change_permission = has_change_permission

    # Patch backend to handle results from revoked tasks.
    from django_celery_results.backends.database import DatabaseBackend

    _original_store_result = DatabaseBackend._store_result

    def _store_result(self, task_id, result, status, traceback=None, request=None):
        # Handle "revoked" tasks that get a slightly different request object.
        if hasattr(request, '_payload'):
            request._task_obj = request.task
            request.task = request._task_obj.name
            request.args = request._payload[0]
            request.kwargs = request._payload[1]
        return _original_store_result(self, task_id, result, status, traceback, request)

    DatabaseBackend._store_result = _store_result

    # Patch backend to handle exception results.
    def encode_result(self, result, state):
        if state in self.EXCEPTION_STATES and isinstance(result, Exception):
            result = self.prepare_exception(result)
            if isinstance(result, dict) and 'exc_message' in result:
                try:
                    self._encode(result['exc_message'])
                except Exception:
                    if isinstance(result['exc_message'], (list, tuple)):
                        result['exc_message'] = list(map(str, result['exc_message']))
                    else:
                        result['exc_message'] = str(result['exc_message'])
            return result
        else:
            return self.prepare_value(result)

    DatabaseBackend.encode_result = encode_result
