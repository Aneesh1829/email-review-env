---
title: Email Review Env
emoji: "📧"
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 📧 Email Review Environment

An OpenEnv environment where an AI agent learns to triage and respond to real-world customer support emails.

## What This Environment Does

The agent is shown customer support emails one at a time. For each email it must:
1. **Categorize** it — billing / technical / general / complaint
2. **Prioritize** it — low / medium / high / urgent
3. **Draft a reply** — a professional, empathetic response

## Tasks (Easy → Medium → Hard)

| Task | Difficulty | Scenario |
|------|-----------|----------|
| 1 | Easy | Double billing charge |
| 2 | Medium | Angry premium subscriber outage |
| 3 | Hard | API auth failure + wrong billing tier |

## Action Space
```python
EmailAction(
    category    = "billing",
    priority    = "high",
    reply_draft = "Dear customer..."
)
```

## Observation Space
```python
EmailObservation(
    email_subject = "Invoice question",
    email_body    = "I was charged twice...",
    sender_name   = "Priya Sharma",
    last_score    = 0.75,
    done          = False,
    reward        = 0.75
)
```

## Setup
```bash
pip install openenv-core fastapi uvicorn pydantic openai websockets
uvicorn server.app:app --host 0.0.0.0 --port 7860
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| API_BASE_URL | LLM API endpoint |
| MODEL_NAME | Model identifier |
| HF_TOKEN | Hugging Face token |
