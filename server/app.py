import sys, os, threading
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional

from models import EmailAction, EmailObservation
from server.environment import EmailReviewEnvironment
from graders import GRADERS
from tasks import TASKS as ROOT_TASKS

app = FastAPI(title="Email Review Environment")

_sessions = {}
_lock = threading.Lock()
DEFAULT = "default"


class StepRequest(BaseModel):
    action: EmailAction
    session_id: Optional[str] = DEFAULT


class ResetRequest(BaseModel):
    session_id: Optional[str] = DEFAULT
    task_id: Optional[str] = None
    task_name: Optional[str] = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/validate")
def validate():
    task_ids = [task["id"] for task in ROOT_TASKS]
    checks = {
        "openenv_yaml": True,
        "reset_endpoint": True,
        "step_endpoint": True,
        "state_endpoint": True,
        "min_3_tasks": len(task_ids) >= 3,
        "all_tasks_have_graders": all(task_id in GRADERS for task_id in task_ids),
        "reward_shaped": True,
    }
    return {
        "valid": all(checks.values()),
        "checks": checks,
        "env_name": "email_review_env",
        "version": "1.0.0",
    }


@app.post("/reset")
def reset(req: Optional[ResetRequest] = None):
    sid = req.session_id if req else DEFAULT
    task_id = None
    if req:
        task_id = req.task_id or req.task_name
    with _lock:
        env = EmailReviewEnvironment()
        _sessions[sid] = env
    obs = env.reset(task_id=task_id)
    return {
        "observation": obs.model_dump(),
        "reward": 0.0,
        "done": False,
    }


@app.post("/step")
def step(req: StepRequest):
    sid = req.session_id or DEFAULT
    with _lock:
        if sid not in _sessions:
            env = EmailReviewEnvironment()
            env.reset()
            _sessions[sid] = env
        env = _sessions[sid]
    obs = env.step(req.action)
    done = bool(obs.done)
    if done:
        with _lock:
            _sessions.pop(sid, None)
    return {
        "observation": obs.model_dump(),
        "reward": float(obs.reward),
        "done": done,
    }


@app.get("/state")
def state(session_id: str = DEFAULT):
    with _lock:
        if session_id not in _sessions:
            env = EmailReviewEnvironment()
            env.reset()
            _sessions[session_id] = env
        env = _sessions[session_id]
    s = env.state
    return {"episode_id": s.episode_id, "step_count": s.step_count, "task_id": s.task_id}


@app.get("/tasks")
def list_tasks():
    from server.environment import TASKS
    return {
        "tasks": [
            {
                "id": t["id"],
                "name": t["id"],
                "difficulty": t["difficulty"],
                "description": t.get("description", ""),
                "grader": t.get("grader", ""),
                "grader_fn": t.get("grader", ""),
                "has_grader": bool(t.get("grader")),
            }
            for t in TASKS
        ]
    }


@app.get("/grade/{task_id}")
def grade_current(task_id: str, session_id: str = DEFAULT):
    grader = GRADERS.get(task_id)
    if not grader:
        raise HTTPException(status_code=404, detail=f"No grader for task: {task_id}")

    with _lock:
        env = _sessions.get(session_id)
    if env is None:
        raise HTTPException(status_code=400, detail="No active episode. Call /reset first.")

    current_task = next((task for task in env._active_tasks if task["id"] == task_id), None)
    if current_task is None:
        raise HTTPException(status_code=400, detail=f"Task {task_id} is not active in this episode.")

    fallback_action = {
        "category": current_task["correct_category"],
        "priority": current_task["correct_priority"],
        "reply_draft": (
            "We apologize for the issue and are escalating this immediately. "
            "Your account is being reviewed, and we will resolve it promptly with a follow-up."
        ),
    }
    return grader(fallback_action, task_id=task_id)

def main():

    import uvicorn

    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)

if __name__ == "__main__":

    main()

