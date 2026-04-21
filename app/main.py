from __future__ import annotations

from contextlib import asynccontextmanager
from typing import List

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import orm_models  # ensures models are registered with Base
from app.db.db import Base, engine as db_engine, get_db_session
from app.engine import WorkflowEngine
from app.models import (
    AuditEventResponse,
    DecisionPayload,
    Role,
    WorkflowRequestCreate,
    WorkflowRequestResponse,
    WorkflowRequestUpdate,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with db_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title="AI Workflow Orchestrator",
    description="Enterprise workflow orchestration API with approvals, SLA escalation, audit logging, and AI enrichment.",
    version="1.0.0",
    lifespan=lifespan,
)


class EscalationPayload(BaseModel):
    actor_name: str
    actor_role: Role
    reason: str


@app.get("/health")
async def health_check():
    return {"status": "ok"}


@app.post("/requests", response_model=WorkflowRequestResponse)
async def create_request(
    payload: WorkflowRequestCreate,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.create_request(payload)
    return WorkflowRequestResponse.from_entity(request)


@app.get("/requests", response_model=List[WorkflowRequestResponse])
async def list_requests(
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    requests = await workflow_engine.list_requests()
    return [WorkflowRequestResponse.from_entity(r) for r in requests]


@app.get("/requests/{request_id}", response_model=WorkflowRequestResponse)
async def get_request(
    request_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.get_request(request_id)
    return WorkflowRequestResponse.from_entity(request)


@app.patch("/requests/{request_id}", response_model=WorkflowRequestResponse)
async def update_request(
    request_id: str,
    payload: WorkflowRequestUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.update_request(request_id, payload)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/enrich", response_model=WorkflowRequestResponse)
async def enrich_request(
    request_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.enrich_request(request_id)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/submit", response_model=WorkflowRequestResponse)
async def submit_request(
    request_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.submit_request(request_id)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/approve", response_model=WorkflowRequestResponse)
async def approve_request(
    request_id: str,
    payload: DecisionPayload,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.approve_request(request_id, payload)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/reject", response_model=WorkflowRequestResponse)
async def reject_request(
    request_id: str,
    payload: DecisionPayload,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.reject_request(request_id, payload)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/escalate", response_model=WorkflowRequestResponse)
async def escalate_request(
    request_id: str,
    payload: EscalationPayload,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    request = await workflow_engine.escalate_request(
        request_id,
        payload.actor_name,
        payload.actor_role,
        payload.reason,
    )
    return WorkflowRequestResponse.from_entity(request)


@app.post("/sla/run")
async def run_sla_check(
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    escalated = await workflow_engine.auto_escalate_breached_requests()
    return {
        "escalated_count": len(escalated),
        "request_ids": [r.id for r in escalated],
    }


@app.get("/requests/{request_id}/audit", response_model=List[AuditEventResponse])
async def get_audit_log(
    request_id: str,
    db: AsyncSession = Depends(get_db_session),
):
    workflow_engine = WorkflowEngine(db)
    events = await workflow_engine.get_audit_log(request_id)
    return [AuditEventResponse.from_entity(e) for e in events]

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
