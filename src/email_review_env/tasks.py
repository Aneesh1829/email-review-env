try:
    from .graders import GRADERS
except ImportError:
    from graders import GRADERS

from server.environment import TASKS as SERVER_TASKS


def _normalize_task(task):
    grader_ref = task["grader"]
    grader_callable = GRADERS[task["id"]]
    return {
        "id": task["id"],
        "name": task["id"],
        "difficulty": task["difficulty"],
        "description": task.get("description", task.get("task_description", "")),
        "grader": grader_callable,
        "grader_callable": grader_callable,
        "grader_fn": grader_ref,
        "grader_ref": grader_ref,
        "grader_name": grader_callable.__name__,
        "module": grader_callable.__module__,
    }


TASKS = [_normalize_task(task) for task in SERVER_TASKS]
TASK_MAP = {task["id"]: task for task in TASKS}
TASK_REGISTRY = TASK_MAP
