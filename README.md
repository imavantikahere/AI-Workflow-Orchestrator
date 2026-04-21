# AI-Workflow-Orchestrator

An end-to-end production level AI-powered workflow management system that automates request classification, approval routing, and decision-making using Large Language Models. It is designed to demonstrate how AI can be embedded into real business processes.


🔗 **Live Demo (Frontend):** https://ai-workflow-orchestrator-avantika.streamlit.app  
🔗 **Backend API (SwaggerUI):** https://ai-workflow-orchestrator.onrender.com/docs


## Features

- LLM-powered request classification & enrichment
- Dynamic approval chain generation
- Workflow engine with state transitions
- Streamlit dashboard for request management
- Full-stack deployment (FastAPI (Render) + Streamlit)

# This project is built in three phases:

1. In-memory workflow engine for rapid prototyping (Completed)
   No database - only Python data structures for storing in session requests and audit logs
   Focus: To understand workflow logic clearly and keep moving fast - I am still learning fundamentals of AI and backend programming. 
2. Database-backed architecture using SQLAlchemy (Completed)
   Focus: Persistence, real audit trails, and production-style backend architecture with complete manual SwaggerUI testing
3. Front interface integration using Streamlit (Completed)
   Focus: To connect backend with frontend and to create an integrated user friendly system
4. Deployment using Render (for FastAPI backend) and Streamlit for frontend (Completed)

# System Architecture

<img width="1536" height="1024" alt="ChatGPT Image Feb 17, 2026 at 04_26_11 PM" src="https://github.com/user-attachments/assets/3d1630ef-57ca-4d72-bba3-89add840a90a" />

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
2. FastAPI — REST API + Swagger UI 
3. Pydantic — request/response validation
* AI / LLM Layer
1. OpenAI (Responses API) or Groq (swappable provider)
2. Structured output enforced with JSON schema 
* Database (Phase 2)
1. SQLite (local dev) using:
2. SQLAlchemy (async) + aiosqlite
* Deployment (Phase 3 and 4)
1. Streamlit for frontend UI and deployment
2. Render for FASTAPI backend deployment 

## Deployment Lessons Learned

[Read detailed lessons](AI_Workflow_Deployment_Lessons.pdf)

# How to run the Project

## Deployed, ready made demo links:

**Live Demo (Frontend):** https://ai-workflow-orchestrator-avantika.streamlit.app  
**Backend API (Swagger):** https://ai-workflow-orchestrator.onrender.com/docs

---

## LOCAL SETUP 

Before local setup, make sure BASE URL in api_client.py corresponds to localhost and local database. Comments are added in code for easy setup.

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

## Future Improvements

- Migrate to Postgres for persistent storage
- Add authentication & user roles/ access based system
- Improve UI/UX of Streamlit dashboard
- Add more analytics and reporting features
- Expand LLM capabilities (multi-agent workflows)

