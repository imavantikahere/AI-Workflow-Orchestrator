from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import AuditEventORM, WorkflowRequestORM
from app.models import AuditEvent, AuditAction, RequestState, RequestType, Role, WorkflowRequest


def orm_to_request(row: WorkflowRequestORM) -> WorkflowRequest:
    return WorkflowRequest(
        id=row.id,
        title=row.title,
        description=row.description,
        created_by=row.created_by,
        request_type=RequestType(row.request_type),
        state=RequestState(row.state),
        amount=row.amount,
        leave_days=row.leave_days,
        severity=row.severity,
        summary=row.summary,
        ai_confidence=row.ai_confidence,
        approval_chain=[Role(item) for item in json.loads(row.approval_chain)],
        approval_index=row.approval_index,
        created_at=row.created_at,
        updated_at=row.updated_at,
        sla_deadline=row.sla_deadline,
    )


def request_to_orm(request: WorkflowRequest) -> WorkflowRequestORM:
    return WorkflowRequestORM(
        id=request.id,
        title=request.title,
        description=request.description,
        created_by=request.created_by,
        request_type=request.request_type.value,
        state=request.state.value,
        amount=request.amount,
        leave_days=request.leave_days,
        severity=request.severity,
        summary=request.summary,
        ai_confidence=request.ai_confidence,
        approval_chain=json.dumps([r.value for r in request.approval_chain]),
        approval_index=request.approval_index,
        created_at=request.created_at,
        updated_at=request.updated_at,
        sla_deadline=request.sla_deadline,
    )


class WorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_request(self, request: WorkflowRequest) -> WorkflowRequest:
        row = request_to_orm(request)
        self.session.add(row)
        await self.session.commit()
        return request

    async def get_request(self, request_id: str) -> Optional[WorkflowRequest]:
        result = await self.session.execute(
            select(WorkflowRequestORM).where(WorkflowRequestORM.id == request_id)
        )
        row = result.scalar_one_or_none()
        return orm_to_request(row) if row else None

    async def list_requests(self) -> List[WorkflowRequest]:
        result = await self.session.execute(select(WorkflowRequestORM))
        rows = result.scalars().all()
        return [orm_to_request(row) for row in rows]

    async def add_audit_event(self, event: AuditEvent) -> None:
        row = AuditEventORM(
            id=event.id,
            request_id=event.request_id,
            timestamp=event.timestamp,
            actor_name=event.actor_name,
            actor_role=event.actor_role.value,
            action=event.action.value,
            from_state=event.from_state.value if event.from_state else None,
            to_state=event.to_state.value if event.to_state else None,
            comments=event.comments,
            metadata_json=json.dumps(event.metadata),
        )
        self.session.add(row)
        await self.session.commit()

    async def get_audit_events(self, request_id: str) -> List[AuditEvent]:
        result = await self.session.execute(
            select(AuditEventORM).where(AuditEventORM.request_id == request_id)
        )
        rows = result.scalars().all()
        return [
            AuditEvent(
                id=row.id,
                request_id=row.request_id,
                timestamp=row.timestamp,
                actor_name=row.actor_name,
                actor_role=Role(row.actor_role),
                action=AuditAction(row.action),
                from_state=RequestState(row.from_state) if row.from_state else None,
                to_state=RequestState(row.to_state) if row.to_state else None,
                comments=row.comments,
                metadata=json.loads(row.metadata_json),
            )
            for row in rows
        ]
