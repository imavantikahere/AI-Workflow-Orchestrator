# AI Workflow Orchestrator

A starter FastAPI backend for enterprise-style workflow orchestration with:
- request creation and editing
- AI enrichment
- multi-step approval chains
- role-based approvals
- SLA-based escalation
- audit logging

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
python run.py
```

Open Swagger at:

```txt
http://127.0.0.1:8000/docs
```

## Test

```bash
pytest
```

## Notes
- The API currently uses in-memory storage for the working flow.
- A Phase 2 async SQLAlchemy DB layer is included under `app/db/`.
- To enable real LLM enrichment, set `OPENAI_API_KEY` in your environment.
