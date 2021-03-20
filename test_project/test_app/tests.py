# pytest
import pytest

# Celery
from celery import shared_task

# Celery-Task-Plus
from celery_task_plus.tasks import LockedTask


@pytest.mark.parametrize('task_key_name,task_key_args,task_key_kwargs,task_name,task_args,task_kwargs,task_key', [
    (True, True, True, 'task_name1', (), {}, 'task-name1'),
    (True, True, True, 'task_name2', (1,), {}, 'task-name2-1'),
    (True, True, True, 'task_name3', (1,), {'q': 3}, 'task-name3-1-q3'),
    (True, True, True, 'task_name4', (), {'q': 3}, 'task-name4-q3'),
    ('alt_task_name1', True, True, 'task_name5', (), {}, 'alt-task-name1'),
    ('alt_task_name2', True, True, 'task_name6', (1,), {}, 'alt-task-name2-1'),
    ('alt_task_name3', True, True, 'task_name7', (1,), {'q': 3}, 'alt-task-name3-1-q3'),
    ('alt_task_name4', True, True, 'task_name8', (), {'q': 3}, 'alt-task-name4-q3'),
    (False, True, True, 'task_name9', (), {}, ''),
    (False, True, True, 'task_name10', (1,), {}, '-1'),
    (False, True, True, 'task_name11', (1,), {'q': 3}, '-1-q3'),
    (False, True, True, 'task_name12', (), {'q': 3}, '-q3'),
    (True, False, True, 'task_name13', (), {}, 'task-name13'),
    (True, False, True, 'task_name14', (1,), {}, 'task-name14'),
    (True, False, True, 'task_name15', (1,), {'q': 3}, 'task-name15-q3'),
    (True, False, True, 'task_name16', (), {'q': 3}, 'task-name16-q3'),
    (True, 1, True, 'task_name17', (), {}, 'task-name17'),
    (True, 1, True, 'task_name18', (1,), {}, 'task-name18-1'),
    (True, 1, True, 'task_name19', (1, 2,), {}, 'task-name19-1'),
    (True, 1, True, 'task_name20', (1,), {'q': 3}, 'task-name20-1-q3'),
    (True, 1, True, 'task_name21', (), {'q': 3}, 'task-name21-q3'),
    (True, True, False, 'task_name22', (), {}, 'task-name22'),
    (True, True, False, 'task_name23', (1,), {}, 'task-name23-1'),
    (True, True, False, 'task_name24', (1,), {'q': 3}, 'task-name24-1'),
    (True, True, False, 'task_name25', (), {'q': 3}, 'task-name25'),
    (True, True, (), 'task_name26', (), {}, 'task-name26'),
    (True, True, (), 'task_name27', (1,), {}, 'task-name27-1'),
    (True, True, (), 'task_name28', (1,), {'q': 3}, 'task-name28-1'),
    (True, True, (), 'task_name29', (), {'q': 3}, 'task-name29'),
    (True, True, ('q',), 'task_name30', (), {}, 'task-name30'),
    (True, True, ('q',), 'task_name31', (1,), {}, 'task-name31-1'),
    (True, True, ('q',), 'task_name32', (1,), {'q': 3}, 'task-name32-1-q3'),
    (True, True, ('q',), 'task_name33', (), {'q': 3}, 'task-name33-q3'),
    (True, True, ('q',), 'task_name34', (), {'z': 5}, 'task-name34'),
    (True, True, ('q', 'z',), 'task_name35', (), {'q': 3, 'z': 5}, 'task-name35-q3-z5'),
])
def test_get_task_key(task_key_name, task_key_args, task_key_kwargs, task_name, task_args, task_kwargs, task_key):

    def task_func(*args, **kwargs):
        pass

    task_class = shared_task(
        base=LockedTask,
        name=task_name,
        task_key_name=task_key_name,
        task_key_args=task_key_args,
        task_key_kwargs=task_key_kwargs,
    )(task_func)

    generated_task_key = task_class._get_task_key(*task_args, **task_kwargs)
    assert generated_task_key == task_key
