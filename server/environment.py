"""
server/environment.py
---------------------
THE BRAIN of the environment. This is where all the logic lives.

It contains:
- 3 email tasks (Easy → Medium → Hard) as required by the contest
- A reward/grader function for each task
- reset() to start fresh
- step() to process the AI's answer and return a score

TASK DIFFICULTY:
  Task 1 (Easy)   - Simple billing question, obvious category & priority
  Task 2 (Medium) - Angry complaint, needs correct tone + priority judgment
  Task 3 (Hard)   - Complex technical + billing combo, requires precise reply
"""

import re
from uuid import uuid4
from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models import EmailAction, EmailObservation


# ---------------------------------------------------------------------------
# Task definitions
# Each task is a dict with:
#   email_*      : the email content shown to the agent
#   correct_*    : ground truth for grading
#   required_*   : keywords that MUST appear in the reply
#   forbidden_*  : words/phrases that should NOT appear
#   difficulty   : "easy" | "medium" | "hard"
# ---------------------------------------------------------------------------
TASKS = [
    # ── Task 1: EASY ──────────────────────────────────────────────────────
    {
        "id": "task_1_easy",
        "difficulty": "easy",
        "sender_name": "Priya Sharma",
        "email_subject": "Invoice question",
        "email_body": (
            "Hi, I received my invoice for this month and noticed I was charged "
            "twice for the same subscription. The amount is ₹499 × 2 = ₹998. "
            "Could you please look into this and refund the extra charge? "
            "My account ID is #84721. Thank you."
        ),
        "task_description": (
            "Task 1 (Easy): Categorize this email correctly, set the right priority, "
            "and draft a polite reply that acknowledges the double charge issue, "
            "mentions the account ID, and promises a resolution."
        ),
        "correct_category": "billing",
        "correct_priority": "high",           # double charge = high priority
        "required_keywords": ["refund", "account", "apologize"],
        "forbidden_phrases": ["cannot help", "not our problem"],
        "min_reply_length": 40,               # words
    },

    # ── Task 2: MEDIUM ────────────────────────────────────────────────────
    {
        "id": "task_2_medium",
        "difficulty": "medium",
        "sender_name": "Ravi Menon",
        "email_subject": "EXTREMELY FRUSTRATED - service has been down for 3 days!!!",
        "email_body": (
            "I am absolutely furious. Your service has been completely down for "
            "THREE DAYS and no one has responded to any of my support tickets. "
            "I am a premium subscriber paying ₹2999/month. This is completely "
            "unacceptable. I want a full refund for this month AND compensation. "
            "If this is not resolved TODAY I am cancelling my account and posting "
            "reviews everywhere. This is a DISASTER for my business."
        ),
        "task_description": (
            "Task 2 (Medium): This is an angry premium customer with a service outage. "
            "Categorize correctly (this has BOTH technical and complaint elements — "
            "pick the dominant one), set urgent priority (premium customer + business impact), "
            "and draft a reply that de-escalates, acknowledges the frustration specifically, "
            "offers a concrete next step, and does NOT sound like a template."
        ),
        "correct_category": "complaint",      # dominant theme is complaint/frustration
        "correct_priority": "urgent",         # premium subscriber + business impact
        "required_keywords": ["apologize", "escalat", "premium", "resolve"],
        "forbidden_phrases": ["we understand your frustration", "valued customer", "at your earliest convenience"],
        "min_reply_length": 60,
    },

    # ── Task 3: HARD ──────────────────────────────────────────────────────
    {
        "id": "task_3_hard",
        "difficulty": "hard",
        "sender_name": "Ananya Krishnan",
        "email_subject": "API authentication failing + wrong billing tier",
        "email_body": (
            "Hello, I'm facing two separate issues:\n\n"
            "1. TECHNICAL: Our API calls have been failing with error 401 since "
            "yesterday after we rotated our API keys using your dashboard. The "
            "new key returns 'Invalid signature' even though we followed the docs exactly. "
            "We've tried regenerating twice — same error.\n\n"
            "2. BILLING: We were supposed to be on the Enterprise tier (₹15,000/month) "
            "but our invoice shows we're being charged for the Business tier (₹7,500/month). "
            "This means our SLA guarantees and dedicated support are also not active.\n\n"
            "We need both fixed urgently. Our team of 50 engineers are blocked. "
            "CTO is aware. Account: ENT-00291."
        ),
        "task_description": (
            "Task 3 (Hard): Complex dual-issue email with BOTH technical (API 401 error) "
            "and billing (wrong tier) problems. Category should reflect the most blocking issue. "
            "Priority must be urgent (50 engineers blocked, CTO involved). "
            "Reply MUST address BOTH issues separately, include the account number, "
            "mention specific technical steps AND billing escalation path, be professional "
            "and detailed. Minimum 100 words."
        ),
        "correct_category": "technical",      # API blocking 50 engineers = more urgent
        "correct_priority": "urgent",
        "required_keywords": ["401", "api", "billing", "enterprise", "account", "escalat"],
        "forbidden_phrases": ["we cannot", "not possible"],
        "min_reply_length": 100,
    },
]


# ---------------------------------------------------------------------------
# Grader: scores a single task action (0.0 → 1.0)
# Partial credit is intentional — this satisfies "partial progress signals"
# ---------------------------------------------------------------------------
def grade_action(task: dict, action: EmailAction) -> tuple[float, str]:
    """
    Returns (score: float, breakdown: str)
    Score is between 0.0 and 1.0 with partial credit.

    Scoring breakdown:
      Category correct   : 0.25 points
      Priority correct   : 0.25 points
      Required keywords  : up to 0.30 points (proportional)
      No forbidden phrases: 0.10 points
      Reply length OK    : 0.10 points
    """
    score = 0.0
    notes = []

    # 1. Category check (0.25)
    if action.category.lower().strip() == task["correct_category"]:
        score += 0.25
        notes.append(f"✅ Category correct ({action.category}): +0.25")
    else:
        notes.append(
            f"❌ Category wrong — got '{action.category}', expected '{task['correct_category']}': +0.00"
        )

    # 2. Priority check (0.25)
    if action.priority.lower().strip() == task["correct_priority"]:
        score += 0.25
        notes.append(f"✅ Priority correct ({action.priority}): +0.25")
    else:
        notes.append(
            f"❌ Priority wrong — got '{action.priority}', expected '{task['correct_priority']}': +0.00"
        )

    # 3. Required keywords in reply (0.30 proportional)
    reply_lower = action.reply_draft.lower()
    found_keywords = [
        kw for kw in task["required_keywords"]
        if kw.lower() in reply_lower
    ]
    keyword_ratio = len(found_keywords) / max(len(task["required_keywords"]), 1)
    keyword_score = round(keyword_ratio * 0.30, 3)
    score += keyword_score
    notes.append(
        f"{'✅' if keyword_ratio == 1.0 else '⚠️'} Keywords found "
        f"{len(found_keywords)}/{len(task['required_keywords'])} "
        f"({found_keywords}): +{keyword_score}"
    )

    # 4. No forbidden phrases (0.10)
    forbidden_found = [
        fp for fp in task["forbidden_phrases"]
        if fp.lower() in reply_lower
    ]
    if not forbidden_found:
        score += 0.10
        notes.append("✅ No forbidden phrases: +0.10")
    else:
        notes.append(f"❌ Forbidden phrases found {forbidden_found}: +0.00")

    # 5. Reply length (0.10)
    reply_word_count = len(action.reply_draft.split())
    if reply_word_count >= task["min_reply_length"]:
        score += 0.10
        notes.append(f"✅ Reply length OK ({reply_word_count} words): +0.10")
    else:
        notes.append(
            f"❌ Reply too short — {reply_word_count} words, need {task['min_reply_length']}: +0.00"
        )

    score = round(min(score, 1.0), 3)
    breakdown = "\n".join(notes) + f"\n\nFINAL SCORE: {score}"
    return score, breakdown


# ---------------------------------------------------------------------------
# The Environment class — this is what OpenEnv calls
# ---------------------------------------------------------------------------
class EmailReviewEnvironment(Environment):
    """
    Email Triage & Response Environment.

    An AI agent is shown customer support emails one by one.
    For each email it must: categorize, prioritize, and draft a reply.
    It receives a score (0.0 → 1.0) after each submission.

    3 tasks: Easy → Medium → Hard
    """

    def __init__(self):
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task_index = 0
        self._task_scores = []

    def reset(self) -> EmailObservation:
        """Start a fresh episode from Task 1."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._current_task_index = 0
        self._task_scores = []

        task = TASKS[0]
        return EmailObservation(
            email_subject=task["email_subject"],
            email_body=task["email_body"],
            sender_name=task["sender_name"],
            task_description=task["task_description"],
            last_score=0.0,
            score_breakdown="",
            task_completed=False,
            done=False,
            reward=0.0,
        )

    def step(self, action: EmailAction) -> EmailObservation:
        """
        Process the agent's action for the current task.
        Grade it, move to the next task (or finish if all done).
        """
        self._state.step_count += 1
        task = TASKS[self._current_task_index]

        # Grade the action
        score, breakdown = grade_action(task, action)
        self._task_scores.append(score)

        # Move to next task
        self._current_task_index += 1
        all_done = self._current_task_index >= len(TASKS)

        if all_done:
            avg_score = round(sum(self._task_scores) / len(self._task_scores), 3)
            return EmailObservation(
                email_subject="All tasks complete",
                email_body=(
                    f"Episode finished!\n"
                    f"Task scores: {self._task_scores}\n"
                    f"Average score: {avg_score}"
                ),
                sender_name="System",
                task_description="Episode complete. Call reset() to start again.",
                last_score=score,
                score_breakdown=breakdown,
                task_completed=True,
                done=True,
                reward=score,
            )
        else:
            next_task = TASKS[self._current_task_index]
            return EmailObservation(
                email_subject=next_task["email_subject"],
                email_body=next_task["email_body"],
                sender_name=next_task["sender_name"],
                task_description=next_task["task_description"],
                last_score=score,
                score_breakdown=breakdown,
                task_completed=False,
                done=False,
                reward=score,
            )

    @property
    def state(self) -> State:
        return self._state
