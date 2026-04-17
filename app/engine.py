from __future__ import annotations

from datetime import timedelta
from typing import List

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai_llm import ai_service
from app.db.repository import WorkflowRepository
from app.models import (
    AuditAction,
    AuditEvent,
    DecisionPayload,
    RequestState,
    RequestType,
    Role,
    WorkflowRequest,
    WorkflowRequestCreate,
    WorkflowRequestUpdate,
    new_audit_id,
    new_request_id,
    utc_now,
)



class WorkflowEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.repo = WorkflowRepository(session)


    async def create_request(self, payload: WorkflowRequestCreate) -> WorkflowRequest:
        request = WorkflowRequest(
            id=new_request_id(),
            title=payload.title,
            description=payload.description,
            created_by=payload.created_by,
            request_type=payload.request_type,
            amount=payload.amount,
            leave_days=payload.leave_days,
            severity=payload.severity,
        )

        await self.repo.create_request(request)

        await self._log_event(
            request_id=request.id,
            actor_name=payload.created_by,
            actor_role=Role.EMPLOYEE,
            action=AuditAction.CREATED,
            from_state=None,
            to_state=request.state,
            comments="Request created",
        )
        return request

    async def list_requests(self) -> List[WorkflowRequest]:
        return await self.repo.list_requests()

    async def get_request(self, request_id: str) -> WorkflowRequest:
        request = await self.repo.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        return request

    async def update_request(self, request_id: str, payload: WorkflowRequestUpdate) -> WorkflowRequest:
        request = await self.get_request(request_id)

        if request.state != RequestState.DRAFT:
            raise HTTPException(status_code=400, detail="Only DRAFT requests can be edited")

        original_state = request.state

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(request, field, value)

        request.updated_at = utc_now()
        await self.repo.update_request_record(request)

        await self._log_event(
            request_id=request.id,
            actor_name=request.created_by,
            actor_role=Role.EMPLOYEE,
            action=AuditAction.UPDATED,
            from_state=original_state,
            to_state=request.state,
            comments="Draft updated",
        )
        return request

    async def enrich_request(self, request_id: str) -> WorkflowRequest:
        request = await self.get_request(request_id)
        enrichment = ai_service.enrich_request(request.title, request.description)

        request_type_value = enrichment.get("request_type", "UNKNOWN")
        try:
            request_type_enum = RequestType(request_type_value)
        except ValueError:
            request_type_enum = RequestType.UNKNOWN

        if request.request_type == RequestType.UNKNOWN:
            request.request_type = request_type_enum

        amount = enrichment.get("amount")
        if request.amount is None and isinstance(amount, (int, float)):
            request.amount = float(amount)

        leave_days = enrichment.get("leave_days")
        if request.leave_days is None and isinstance(leave_days, int):
            request.leave_days = leave_days

        sev = enrichment.get("severity")
        if request.severity is None:
            if isinstance(sev, str):
                sev_map = {"low": 1, "medium": 3, "high": 5}
                sev = sev_map.get(sev.lower())

            if isinstance(sev, (int, float)):
                sev = int(sev)
                if 1 <= sev <= 5:
                    request.severity = sev

        summary = enrichment.get("summary")
        if isinstance(summary, str) and summary.strip():
            request.summary = summary
        else:
            request.summary = f"Request received: {request.title}. Review details and route for approval."

        confidence = enrichment.get("confidence")
        if isinstance(confidence, (int, float)):
            request.ai_confidence = max(0.0, min(1.0, float(confidence)))
        else:
            request.ai_confidence = 0.45

        request.updated_at = utc_now()

        await self.repo.update_request_record(request)

        await self._log_event(
            request_id=request.id,
            actor_name="SYSTEM_AI",
            actor_role=Role.ADMIN,
            action=AuditAction.AI_ENRICHED,
            from_state=request.state,
            to_state=request.state,
            comments="Request enriched using AI",
            metadata=enrichment,
        )
        return request
    async def submit_request(self, request_id: str) -> WorkflowRequest:
        request = await self.get_request(request_id)

        if request.state != RequestState.DRAFT:
            raise HTTPException(status_code=400, detail="Only DRAFT requests can be submitted")

        if request.request_type == RequestType.UNKNOWN:
            await self.enrich_request(request_id)
            request = await self.get_request(request_id)

        request.approval_chain = self._build_approval_chain(request)
        if not request.approval_chain:
            raise HTTPException(status_code=400, detail="Could not determine approval chain")

        request.state = RequestState.IN_REVIEW
        request.approval_index = 0
        request.updated_at = utc_now()
        request.sla_deadline = utc_now() + timedelta(hours=24)

        await self.repo.update_request_record(request)

        await self._log_event(
            request_id=request.id,
            actor_name=request.created_by,
            actor_role=Role.EMPLOYEE,
            action=AuditAction.SUBMITTED,
            from_state=RequestState.DRAFT,
            to_state=request.state,
            comments=f"Submitted for review. Next approver: {request.current_required_role}",
        )
        return request

    async def approve_request(self, request_id: str, payload: DecisionPayload) -> WorkflowRequest:
        request = await self.get_request(request_id)

        if request.state != RequestState.IN_REVIEW:
            raise HTTPException(status_code=400, detail="Request is not under review")

        required_role = request.current_required_role
        if payload.actor_role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Approval requires role {required_role}, got {payload.actor_role}",
            )

        from_state = request.state
        request.approval_index += 1

        if request.approval_index >= len(request.approval_chain):
            request.state = RequestState.APPROVED
            request.sla_deadline = None
        else:
            request.state = RequestState.IN_REVIEW
            request.sla_deadline = utc_now() + timedelta(hours=24)

        request.updated_at = utc_now()
        await self.repo.update_request_record(request)

        await self._log_event(
            request_id=request.id,
            actor_name=payload.actor_name,
            actor_role=payload.actor_role,
            action=AuditAction.APPROVED,
            from_state=from_state,
            to_state=request.state,
            comments=payload.comments,
            metadata={"next_required_role": str(request.current_required_role)},
        )
        return request

    async def reject_request(self, request_id: str, payload: DecisionPayload) -> WorkflowRequest:
        request = await self.get_request(request_id)

        if request.state != RequestState.IN_REVIEW:
            raise HTTPException(status_code=400, detail="Request is not under review")

        required_role = request.current_required_role
        if payload.actor_role != required_role:
            raise HTTPException(
                status_code=403,
                detail=f"Rejection requires role {required_role}, got {payload.actor_role}",
            )

        from_state = request.state
        request.state = RequestState.REJECTED
        request.updated_at = utc_now()
        request.sla_deadline = None

        await self.repo.update_request_record(request)

        await self._log_event(
            request_id=request.id,
            actor_name=payload.actor_name,
            actor_role=payload.actor_role,
            action=AuditAction.REJECTED,
            from_state=from_state,
            to_state=request.state,
            comments=payload.comments or "Rejected",
        )
        return request

    async def escalate_request(
        self,
        request_id: str,
        actor_name: str,
        actor_role: Role,
        reason: str,
    ) -> WorkflowRequest:
        request = await self.get_request(request_id)

        if request.state not in {RequestState.IN_REVIEW, RequestState.SUBMITTED}:
            raise HTTPException(
                status_code=400,
                detail="Only submitted or in-review requests can be escalated",
            )

        from_state = request.state
        request.state = RequestState.ESCALATED
        request.updated_at = utc_now()
        request.sla_deadline = None

        await self.repo.update_request_record(request)

        await self._log_event(
            request_id=request.id,
            actor_name=actor_name,
            actor_role=actor_role,
            action=AuditAction.ESCALATED,
            from_state=from_state,
            to_state=request.state,
            comments=reason,
        )
        return request

    async def auto_escalate_breached_requests(self) -> List[WorkflowRequest]:
        escalated: List[WorkflowRequest] = []
        now = utc_now()

        all_requests = await self.repo.list_requests()
        for request in all_requests:
            if (
                request.state == RequestState.IN_REVIEW
                and request.sla_deadline is not None
                and request.sla_deadline < now
            ):
                escalated_request = await self.escalate_request(
                    request_id=request.id,
                    actor_name="SYSTEM_SLA",
                    actor_role=Role.ADMIN,
                    reason="Escalated automatically due to SLA breach",
                )
                escalated.append(escalated_request)

        return escalated

    async def get_audit_log(self, request_id: str):
        await self.get_request(request_id)
        return await self.repo.get_audit_events(request_id)

    def _build_approval_chain(self, request: WorkflowRequest) -> List[Role]:
        if request.request_type == RequestType.PROCUREMENT:
            if (request.amount or 0) > 10000:
                return [Role.MANAGER, Role.FINANCE, Role.DIRECTOR]
            return [Role.MANAGER, Role.FINANCE]

        if request.request_type == RequestType.LEAVE:
            if (request.leave_days or 0) > 3:
                return [Role.MANAGER, Role.HR]
            return [Role.MANAGER]

        if request.request_type == RequestType.SUPPORT:
            if (request.severity or 1) >= 4:
                return [Role.SUPPORT_L2, Role.MANAGER]
            return [Role.SUPPORT_L2]

        return []

    async def _log_event(
        self,
        request_id: str,
        actor_name: str,
        actor_role: Role,
        action: AuditAction,
        from_state,
        to_state,
        comments: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        event = AuditEvent(
            id=new_audit_id(),
            request_id=request_id,
            timestamp=utc_now(),
            actor_name=actor_name,
            actor_role=actor_role,
            action=action,
            from_state=from_state,
            to_state=to_state,
            comments=comments,
            metadata=metadata or {},
        )
        await self.repo.add_audit_event(event)
