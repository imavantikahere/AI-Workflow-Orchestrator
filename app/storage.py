from __future__ import annotations

from typing import Dict, List, Optional

from app.models import AuditEvent, WorkflowRequest


class InMemoryStore:
    def __init__(self) -> None:
        self.requests: Dict[str, WorkflowRequest] = {}
        self.audit_logs: Dict[str, List[AuditEvent]] = {}

    def save_request(self, request: WorkflowRequest) -> WorkflowRequest:
        self.requests[request.id] = request
        return request

    def get_request(self, request_id: str) -> Optional[WorkflowRequest]:
        return self.requests.get(request_id)

    def list_requests(self) -> List[WorkflowRequest]:
        return list(self.requests.values())

    def add_audit_event(self, event: AuditEvent) -> None:
        if event.request_id not in self.audit_logs:
            self.audit_logs[event.request_id] = []
        self.audit_logs[event.request_id].append(event)

    def get_audit_events(self, request_id: str) -> List[AuditEvent]:
        return self.audit_logs.get(request_id, [])


store = InMemoryStore()
