from __future__ import annotations

from typing import List

from fastapi import FastAPI
from pydantic import BaseModel

from app.engine import engine
from app.models import (
    AuditEventResponse,
    DecisionPayload,
    Role,
    WorkflowRequestCreate,
    WorkflowRequestResponse,
    WorkflowRequestUpdate,
)


app = FastAPI(
    title="AI Workflow Orchestrator",
    description="Enterprise workflow orchestration API with approvals, SLA escalation, audit logging, and AI enrichment.",
    version="1.0.0",
)


class EscalationPayload(BaseModel):
    actor_name: str
    actor_role: Role
    reason: str


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/requests", response_model=WorkflowRequestResponse)
def create_request(payload: WorkflowRequestCreate):
    request = engine.create_request(payload)
    return WorkflowRequestResponse.from_entity(request)


@app.get("/requests", response_model=List[WorkflowRequestResponse])
def list_requests():
    return [WorkflowRequestResponse.from_entity(r) for r in engine.list_requests()]


@app.get("/requests/{request_id}", response_model=WorkflowRequestResponse)
def get_request(request_id: str):
    request = engine.get_request(request_id)
    return WorkflowRequestResponse.from_entity(request)


@app.patch("/requests/{request_id}", response_model=WorkflowRequestResponse)
def update_request(request_id: str, payload: WorkflowRequestUpdate):
    request = engine.update_request(request_id, payload)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/enrich", response_model=WorkflowRequestResponse)
def enrich_request(request_id: str):
    request = engine.enrich_request(request_id)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/submit", response_model=WorkflowRequestResponse)
def submit_request(request_id: str):
    request = engine.submit_request(request_id)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/approve", response_model=WorkflowRequestResponse)
def approve_request(request_id: str, payload: DecisionPayload):
    request = engine.approve_request(request_id, payload)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/reject", response_model=WorkflowRequestResponse)
def reject_request(request_id: str, payload: DecisionPayload):
    request = engine.reject_request(request_id, payload)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/requests/{request_id}/escalate", response_model=WorkflowRequestResponse)
def escalate_request(request_id: str, payload: EscalationPayload):
    request = engine.escalate_request(request_id, payload.actor_name, payload.actor_role, payload.reason)
    return WorkflowRequestResponse.from_entity(request)


@app.post("/sla/run")
def run_sla_check():
    escalated = engine.auto_escalate_breached_requests()
    return {
        "escalated_count": len(escalated),
        "request_ids": [r.id for r in escalated],
    }


@app.get("/requests/{request_id}/audit", response_model=List[AuditEventResponse])
def get_audit_log(request_id: str):
    events = engine.get_audit_log(request_id)
    return [AuditEventResponse.from_entity(e) for e in events]
