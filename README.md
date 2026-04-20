# AI-Workflow-Orchestrator
A production-style backend system for orchestrating enterprise workflows with multi-step approvals, SLA-based escalation, audit logging, and LLM-powered request enrichment. Built with FastAPI and designed to demonstrate how AI can be embedded into real business processes.

# This project is built in three phases:

1. In-memory workflow engine for rapid prototyping (Completed)
   No database - only Python data structures for storing in session requests and audit logs
   Focus: To understand workflow logic clearly and keep moving fast - I am still learning fundamentals of AI and backend programming. 
2. Database-backed architecture using SQLAlchemy (Completed)
   Focus: Persistence, real audit trails, and production-style backend architecture with complete manual SwaggerUI testing
3. Front interface integration using Streamlit (Completed)
   Focus: To connect backend with frontend and to create an integrated user friendly system
4. Deployment using cloud based service (In Progress)

# System Architecture

<img width="1536" height="1024" alt="ChatGPT Image Feb 17, 2026 at 04_26_11 PM" src="https://github.com/user-attachments/assets/3d1630ef-57ca-4d72-bba3-89add840a90a" />

# Project Components 
This project shows how to embed AI into a real system:
1. State machine lifecycle (DRAFT → SUBMITTED → IN_REVIEW → APPROVED/REJECTED/ESCALATED)
2. Multi-step approval chains
3. Role-based actions (RBAC-style)
4. Audit logging for traceability
5. SLA and escalation (enterprise requirement)
6. LLM used as a support layer (classification/extraction/summarization)

# User Flow Process

* General Flow 

<img width="1000" height="1500" alt="mermaid-diagram" src="https://github.com/user-attachments/assets/c564f34a-098c-4ccc-89a3-b04a1a8a611f" />

# Project Structure
```text
AI-Workflow-Orchestrator/
│
├── app/                        # Backend (FastAPI)
│   ├── main.py                # Entry point (API routes)
│   ├── models.py              # Data models (Data Structures)
│   ├── engine.py              # Workflow engine (approval logic)
│   ├── ai_llm.py              # LLM enrichment (classification, summary)
│   ├── storage.py             # In-memory storage (for phase 1)
│   │
│   └── db/                    # Database layer (for phase 2)
│       ├── db.py              # DB connection setup
│       ├── orm_models.py      # SQLAlchemy models
│       └── repository.py      # DB operations (CRUD, audit logs)
│
├── frontend/                  # Streamlit frontend
│   ├── streamlit_app.py       # Main app entry (landing page)
│   ├── api_client.py          # Calls for FastAPI backend
│   │
│   └── pages/                 # Multi-page UI
│       ├── 1_Create_Request.py
│       ├── 2_View_Requests.py
│       ├── 3_Request_Details.py
│       └── 4_Approval_Dashboard.py
│
│
├── .streamlit/                # UI config
│   └── config.toml           # Theme settings
│
├── requirements.txt          # Dependencies
├── README.md                 # Project documentation
└── .gitignore
```

# Core Workflow Logic
```text
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
```
# AI / LLM Integration
AI is used for enrichment, not as the source of truth.

# LLM tasks
- Classify request type from free-text (PROCUREMENT / LEAVE / SUPPORT / HR / FINANCE)
- Extract fields when missing (amount, leave days, severity)
- Summarize request for approvers (1–2 sentences)
- Provide a confidence score

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


# How to run the Project

## 1. Clone the repository
```code
git clone https://github.com/imavantikahere/ai-workflow-orchestrator.git
cd ai-workflow-orchestrator
```

## 2. Create a virtual environment
```code
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```

## 3. Install dependencies
```code
pip install -r requirements.txt
```

## 4. Set environment variables (optional but recommended)
```code
For LLM integration
export LLM_PROVIDER=openai
export OPENAI_API_KEY=your_api_key
```
```code
OR for Groq:
export LLM_PROVIDER=groq
export GROQ_API_KEY=your_api_key
```
## 5. Run the FASTAPI server
```code
uvicorn app.main:app --reload
```

## 6. Access the Backend API

Swagger UI (Interactive API Docs): http://127.0.0.1:8000/docs

## 7. Acess the Streamlit frontend 

```code
streamlit run frontend/streamlit_app.py
```

## 8. Accessing the DB

On VStudio, install SQLite Viewer extension and you can view all request entries and audit logs on workflow.db, right below run.py.

Alternatively, on terminal/bash:

```code
sqlite3 workflow.db

SELECT * FROM audit_events
SELECT * FROM workflow_requests

```





## Notes
- Phase 2 has been completed. Phase 3 in progress to add frontend layer.
- To enable real LLM enrichment, set `OPENAI_API_KEY` in your environment.

