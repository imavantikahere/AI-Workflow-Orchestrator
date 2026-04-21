'''models.py is the data-definition file for the project. It defines:
the allowed roles
the allowed request types
the workflow states
the audit actions
the input models for API requests
the internal dataclass objects used by the workflow engine
the response models sent back by FastAPI
helper functions for generating IDs and timestamps
'''

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

#These are the different roles a user can have while using the system
class Role(str, Enum):
    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    FINANCE = "FINANCE"
    DIRECTOR = "DIRECTOR"
    HR= "HR"
    SUPPORT_L2 = "SUPPORT_L2"
    ADMIN = "ADMIN"

#The requests can be classfied into Prcourement, Leave, Support, Finance, HR. UNKNOWN is for AI classification
class RequestType(str, Enum):
    PROCUREMENT = "PROCUREMENT"
    LEAVE = "LEAVE"
    SUPPORT = "SUPPORT"
    FINANCE = "FINANCE"
    HR = "HR"
    UNKNOWN = "UNKNOWN"

#The request can go through different statuses
class RequestState(str, Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"

#The audit holds different status of the logs
class AuditAction(str, Enum):
    CREATED = "CREATED"
    UPDATED = "UPDATED"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"
    AI_ENRICHED = "AI_ENRICHED"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

#Pydantic models to describe data schemas for the API

#This is the input schema used when creating a new request through the API.
class WorkflowRequestCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5, max_length=5000)
    created_by: str = Field(..., min_length=1, max_length=100)
    request_type: RequestType = RequestType.UNKNOWN
    amount: Optional[float] = Field(default=None, ge=0)
    leave_days: Optional[int] = Field(default=None, ge=0)
    severity: Optional[int] = Field(default=None, ge=1, le=5)

    @field_validator("title", "description", "created_by")
    @classmethod
    def strip_text(cls, v: str) -> str:
        return v.strip()

#This is the input schema used when updating a request through the API.
class WorkflowRequestUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    description: Optional[str] = Field(default=None, min_length=5, max_length=5000)
    request_type: Optional[RequestType] = None
    amount: Optional[float] = Field(default=None, ge=0)
    leave_days: Optional[int] = Field(default=None, ge=0)
    severity: Optional[int] = Field(default=None, ge=1, le=5)


class DecisionPayload(BaseModel):
    actor_name: str
    actor_role: Role
    comments: Optional[str] = None


@dataclass
class AuditEvent:
    id: str
    request_id: str
    timestamp: datetime
    actor_name: str
    actor_role: Role
    action: AuditAction
    from_state: Optional[RequestState]
    to_state: Optional[RequestState]
    comments: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowRequest:
    id: str
    title: str
    description: str
    created_by: str
    request_type: RequestType
    state: RequestState = RequestState.DRAFT
    amount: Optional[float] = None
    leave_days: Optional[int] = None
    severity: Optional[int] = None
    summary: Optional[str] = None
    ai_confidence: Optional[float] = None
    approval_chain: List[Role] = field(default_factory=list)
    approval_index: int = 0
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)
    sla_deadline: Optional[datetime] = None

    @property
    def current_required_role(self) -> Optional[Role]:
        if self.approval_index < len(self.approval_chain):
            return self.approval_chain[self.approval_index]
        return None


class WorkflowRequestResponse(BaseModel):
    id: str
    title: str
    description: str
    created_by: str
    request_type: RequestType
    state: RequestState
    amount: Optional[float]
    leave_days: Optional[int]
    severity: Optional[int]
    summary: Optional[str]
    ai_confidence: Optional[float]
    approval_chain: List[Role]
    approval_index: int
    current_required_role: Optional[Role]
    created_at: datetime
    updated_at: datetime
    sla_deadline: Optional[datetime]

    @classmethod
    def from_entity(cls, request: WorkflowRequest) -> "WorkflowRequestResponse":
        return cls(
            id=request.id,
            title=request.title,
            description=request.description,
            created_by=request.created_by,
            request_type=request.request_type,
            state=request.state,
            amount=request.amount,
            leave_days=request.leave_days,
            severity=request.severity,
            summary=request.summary,
            ai_confidence=request.ai_confidence,
            approval_chain=request.approval_chain,
            approval_index=request.approval_index,
            current_required_role=request.current_required_role,
            created_at=request.created_at,
            updated_at=request.updated_at,
            sla_deadline=request.sla_deadline,
        )


class AuditEventResponse(BaseModel):
    id: str
    request_id: str
    timestamp: datetime
    actor_name: str
    actor_role: Role
    action: AuditAction
    from_state: Optional[RequestState]
    to_state: Optional[RequestState]
    comments: Optional[str]
    metadata: Dict[str, Any]

    @classmethod
    def from_entity(cls, event: AuditEvent) -> "AuditEventResponse":
        return cls(**event.__dict__)

#creates a request ID for the entry
def new_request_id() -> str:
    return f"REQ-{uuid4().hex[:10].upper()}"

#returns audit log for the entry
def new_audit_id() -> str:
    return f"AUD-{uuid4().hex[:10].upper()}"

