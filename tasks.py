from server.environment import TASKS as SERVER_TASKS


def _normalize_task(task):
    grader = task["grader"]
    return {
        "id": task["id"],
        "name": task["id"],
        "difficulty": task["difficulty"],
        "description": task.get("description", task.get("task_description", "")),
        "grader": grader,
        "grader_fn": grader,
        "grader_function": grader,
        "grader_name": grader.split(":")[-1],
        "module": grader.split(":")[0],
    }


TASKS = [_normalize_task(task) for task in SERVER_TASKS]
TASK_MAP = {task["id"]: task for task in TASKS}
TASK_REGISTRY = TASK_MAP
