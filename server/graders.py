from __future__ import annotations

from typing import Any

from server.environment import TASKS, grade_action

try:
    from models import EmailAction
except ModuleNotFoundError:
    from email_review_env.models import EmailAction


TASKS_BY_ID = {task["id"]: task for task in TASKS}


def _coerce_action(action: Any) -> EmailAction:
    if isinstance(action, EmailAction):
        return action
    if isinstance(action, dict):
        return EmailAction(**action)
    raise TypeError(f"Unsupported action type for grader: {type(action)!r}")


def _resolve_task(task_id: str | None = None, task: Any = None) -> dict:
    if isinstance(task, dict):
        return task
    if task_id and task_id in TASKS_BY_ID:
        return TASKS_BY_ID[task_id]
    # Fall back to the first configured task so generic validator probes
    # can still import and invoke the shared grader successfully.
    return TASKS[0]


def grade_task(action: Any, task_id: str | None = None, task: Any = None, **_: Any) -> dict:
    resolved_task = _resolve_task(task_id=task_id, task=task)
    resolved_action = _coerce_action(action)
    score, breakdown = grade_action(resolved_task, resolved_action)
    return {
        "score": score,
        "breakdown": breakdown,
        "task_id": resolved_task["id"],
    }


def grade_task_1(action: Any, **kwargs: Any) -> dict:
    return grade_task(action, task_id="task_1_easy", **kwargs)


def grade_task_2(action: Any, **kwargs: Any) -> dict:
    return grade_task(action, task_id="task_2_medium", **kwargs)


def grade_task_3(action: Any, **kwargs: Any) -> dict:
    return grade_task(action, task_id="task_3_hard", **kwargs)
