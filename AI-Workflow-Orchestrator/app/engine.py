from __future__ import annotations

from datetime import timedelta
from typing import List

from fastapi import HTTPException

from app.ai_llm import ai_service
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
from app.storage import store


class WorkflowEngine:
    def create_request(self, payload: WorkflowRequestCreate) -> WorkflowRequest:
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
        store.save_request(request)
        self._log_event(
            request_id=request.id,
            actor_name=payload.created_by,
            actor_role=Role.EMPLOYEE,
            action=AuditAction.CREATED,
            from_state=None,
            to_state=request.state,
            comments="Request created",
        )
        return request

    def list_requests(self) -> List[WorkflowRequest]:
        return store.list_requests()

    def get_request(self, request_id: str) -> WorkflowRequest:
        request = store.get_request(request_id)
        if not request:
            raise HTTPException(status_code=404, detail="Request not found")
        return request

    def update_request(self, request_id: str, payload: WorkflowRequestUpdate) -> WorkflowRequest:
        request = self.get_request(request_id)
        if request.state != RequestState.DRAFT:
            raise HTTPException(status_code=400, detail="Only DRAFT requests can be edited")

        original_state = request.state

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(request, field, value)

        request.updated_at = utc_now()
        store.save_request(request)

        self._log_event(
            request_id=request.id,
            actor_name=request.created_by,
            actor_role=Role.EMPLOYEE,
            action=AuditAction.UPDATED,
            from_state=original_state,
            to_state=request.state,
            comments="Draft updated",
        )
        return request

    def enrich_request(self, request_id: str) -> WorkflowRequest:
        request = self.get_request(request_id)
        enrichment = ai_service.enrich_request(request.title, request.description)

        if request.request_type == RequestType.UNKNOWN:
            request.request_type = RequestType(enrichment["request_type"])
        if request.amount is None and enrichment.get("amount") is not None:
            request.amount = enrichment["amount"]
        if request.leave_days is None and enrichment.get("leave_days") is not None:
            request.leave_days = enrichment["leave_days"]
        if request.severity is None and enrichment.get("severity") is not None:
            
            
            if request.severity is None:
                sev = enrichment.get("severity")

            if isinstance(sev, str):
                sev_map = {"low": 1, "medium": 3, "high": 5}
                sev = sev_map.get(sev.lower())

            if isinstance(sev, int) and 1 <= sev <= 5:
                request.severity = sev

            

        request.summary = enrichment.get("summary")
        request.ai_confidence = enrichment.get("confidence")
        request.updated_at = utc_now()

        store.save_request(request)
        self._log_event(
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

    def submit_request(self, request_id: str) -> WorkflowRequest:
        request = self.get_request(request_id)
        if request.state != RequestState.DRAFT:
            raise HTTPException(status_code=400, detail="Only DRAFT requests can be submitted")

        if request.request_type == RequestType.UNKNOWN:
            self.enrich_request(request_id)
            request = self.get_request(request_id)

        request.approval_chain = self._build_approval_chain(request)
        if not request.approval_chain:
            raise HTTPException(status_code=400, detail="Could not determine approval chain")

        request.state = RequestState.IN_REVIEW
        request.approval_index = 0
        request.updated_at = utc_now()
        request.sla_deadline = utc_now() + timedelta(hours=24)

        store.save_request(request)
        self._log_event(
            request_id=request.id,
            actor_name=request.created_by,
            actor_role=Role.EMPLOYEE,
            action=AuditAction.SUBMITTED,
            from_state=RequestState.DRAFT,
            to_state=request.state,
            comments=f"Submitted for review. Next approver: {request.current_required_role}",
        )
        return request

    def approve_request(self, request_id: str, payload: DecisionPayload) -> WorkflowRequest:
        request = self.get_request(request_id)
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
        store.save_request(request)

        self._log_event(
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

    def reject_request(self, request_id: str, payload: DecisionPayload) -> WorkflowRequest:
        request = self.get_request(request_id)
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
        store.save_request(request)

        self._log_event(
            request_id=request.id,
            actor_name=payload.actor_name,
            actor_role=payload.actor_role,
            action=AuditAction.REJECTED,
            from_state=from_state,
            to_state=request.state,
            comments=payload.comments or "Rejected",
        )
        return request

    def escalate_request(self, request_id: str, actor_name: str, actor_role: Role, reason: str) -> WorkflowRequest:
        request = self.get_request(request_id)
        if request.state not in {RequestState.IN_REVIEW, RequestState.SUBMITTED}:
            raise HTTPException(status_code=400, detail="Only submitted or in-review requests can be escalated")

        from_state = request.state
        request.state = RequestState.ESCALATED
        request.updated_at = utc_now()
        request.sla_deadline = None
        store.save_request(request)

        self._log_event(
            request_id=request.id,
            actor_name=actor_name,
            actor_role=actor_role,
            action=AuditAction.ESCALATED,
            from_state=from_state,
            to_state=request.state,
            comments=reason,
        )
        return request

    def auto_escalate_breached_requests(self) -> List[WorkflowRequest]:
        escalated = []
        now = utc_now()
        for request in store.list_requests():
            if (
                request.state == RequestState.IN_REVIEW
                and request.sla_deadline is not None
                and request.sla_deadline < now
            ):
                escalated.append(
                    self.escalate_request(
                        request_id=request.id,
                        actor_name="SYSTEM_SLA",
                        actor_role=Role.ADMIN,
                        reason="Escalated automatically due to SLA breach",
                    )
                )
        return escalated

    def get_audit_log(self, request_id: str):
        self.get_request(request_id)
        return store.get_audit_events(request_id)

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

    def _log_event(
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
        store.add_audit_event(event)


engine = WorkflowEngine()
