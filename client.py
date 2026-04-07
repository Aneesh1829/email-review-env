"""
client.py
---------
The client is the "remote control" for the environment.
When the AI agent wants to do something, it calls methods on this client.
The client handles all the network communication to the server.

Usage:
    with EmailReviewEnv(base_url="http://localhost:8000").sync() as client:
        obs = client.reset()
        result = client.step(EmailAction(
            category="billing",
            priority="high",
            reply_draft="Dear customer, we apologize..."
        ))
"""

from openenv.core.env_client import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State
from models import EmailAction, EmailObservation


class EmailReviewEnv(EnvClient[EmailAction, EmailObservation, State]):
    """
    Client for the Email Review Environment.
    Connects to the FastAPI server via WebSocket.
    """

    def _step_payload(self, action: EmailAction) -> dict:
        """Convert action object → dict to send over the wire."""
        return {
            "category": action.category,
            "priority": action.priority,
            "reply_draft": action.reply_draft,
        }

    def _parse_result(self, payload: dict) -> StepResult[EmailObservation]:
        """Convert server response dict → StepResult object."""
        obs_data = payload.get("observation", {})
        obs = EmailObservation(
            email_subject=obs_data.get("email_subject", ""),
            email_body=obs_data.get("email_body", ""),
            sender_name=obs_data.get("sender_name", ""),
            task_description=obs_data.get("task_description", ""),
            last_score=obs_data.get("last_score", 0.0),
            score_breakdown=obs_data.get("score_breakdown", ""),
            task_completed=obs_data.get("task_completed", False),
            done=payload.get("done", False),
            reward=payload.get("reward", 0.0),
        )
        return StepResult(
            observation=obs,
            reward=payload.get("reward", 0.0),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: dict) -> State:
        """Convert server state dict → State object."""
        return State(
            episode_id=payload.get("episode_id", ""),
            step_count=payload.get("step_count", 0),
        )
