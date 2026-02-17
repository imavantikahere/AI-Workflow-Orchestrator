# AI-Workflow-Orchestrator
A production-style backend system for orchestrating enterprise workflows with multi-step approvals, SLA-based escalation, audit logging, and LLM-powered request enrichment. Built with FastAPI and designed to demonstrate how AI can be embedded into real business processes.

# This project is built in two phases:
Phase 1: No Database (In-Memory)
Focus: To understand workflow logic clearly and keep moving fast - I am still learning fundamentals of AI and backent programming. 
Phase 2: With Database (SQLite/Postgres-ready)
Focus: Persistence, real audit trails, and production-style architecture - still working on it

# Project Components 
This project shows how to embed AI into a real system:
1. State machine lifecycle (DRAFT → SUBMITTED → IN_REVIEW → APPROVED/REJECTED/ESCALATED)
2. Multi-step approval chains
3. Role-based actions (RBAC-style)
4. Audit logging for traceability
5. SLA and escalation (enterprise requirement)
6. LLM used as a support layer (classification/extraction/summarization)

# Tech Stack
* Core Backend
1. Python 3.10+
2. FastAPI — REST API + Swagger UI at /docs
3. Pydantic — request/response validation
* AI / LLM Layer
1. OpenAI (Responses API) or Azure OpenAI (swappable provider)
2. Structured output enforced with JSON schema (so the backend doesn’t break)
   
* Database (Phase 2)
1. SQLite (local dev) using:
2. SQLAlchemy (async) + aiosqlite

Testing (optional but recommended)
pytest + httpx for API tests

# Project Structure
app/
  models.py        # Enums + Request + AuditEvent dataclasses
  engine.py        # State machine + rules + approvals + audit logic
  main.py          # FastAPI endpoints (calls engine)
  ai_llm.py        # LLM enrichment module (JSON schema output)
  storage.py       # Phase 1 in-memory store
  db/              # Phase 2 database layer (added later)
    db.py
    orm_models.py
    repository.py

<img width="1536" height="1024" alt="ChatGPT Image Feb 17, 2026 at 04_26_11 PM" src="https://github.com/user-attachments/assets/739a8d6c-29e9-4f06-9d77-12a06d5b116e" />


# Models.py
Defines:
1. The types of users (roles)
2. The types of requests
3. The states a request can be in
4. The shape of a request object
5. The shape of an audit log entry

# Engine.py
contains business logic and validates transitions.

# Storage 
handles persistence (memory or DB).

# AI module 
enriches requests but never replaces deterministic rules.

# Core Workflow Logic
States (State Machine)
A request can only be in one state at a time:
DRAFT — created, not submitted
SUBMITTED — submitted for approvals
IN_REVIEW — currently being reviewed by the current approver role
APPROVED — fully approved (all steps passed)
REJECTED — rejected during review (requires reason)
ESCALATED — escalated manually or due to SLA breach

Approval Chains (Multi-step approvals)
Each request gets an approval_chain, e.g.:
Procurement (amount > 10,000): [MANAGER, FINANCE, DIRECTOR]
Leave (days > 3): [MANAGER, HR]
Support (severity 4–5): [SUPPORT_L2, MANAGER]

The engine tracks:
approval_index — which step we’re on
current_required_role() — who must approve next
This mimics real enterprise systems where traceability matters.

# AI / LLM Integration
AI is used for enrichment, not as the source of truth.

# LLM tasks
Classify request type from free-text (PROCUREMENT / LEAVE / SUPPORT)
Extract fields when missing (amount, leave days, severity)
Summarize request for approvers (1–2 sentences)
Provide a confidence score
