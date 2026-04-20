import os
from typing import Any, Dict, Optional

import requests


BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def _handle_response(response: requests.Response) -> Any:
    """
    Safely parse API responses and raise useful errors.
    """
    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        try:
            error_json = response.json()
            raise Exception(f"API Error {response.status_code}: {error_json}") from exc
        except Exception:
            raise Exception(f"API Error {response.status_code}: {response.text}") from exc

    try:
        return response.json()
    except Exception:
        return response.text


def health_check() -> Any:
    """
    Optional backend health check endpoint.
    Adjust path if your backend uses a different route.
    """
    response = requests.get(f"{BASE_URL}/", timeout=10)
    return _handle_response(response)


def create_request(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new workflow request.
    Adjust endpoint if needed.
    """
    response = requests.post(f"{BASE_URL}/requests", json=payload, timeout=20)
    return _handle_response(response)


def get_all_requests() -> Any:
    """
    Fetch all requests.
    """
    response = requests.get(f"{BASE_URL}/requests", timeout=20)
    return _handle_response(response)


def get_request_by_id(request_id: str) -> Dict[str, Any]:
    """
    Fetch a single request by ID.
    """
    response = requests.get(f"{BASE_URL}/requests/{request_id}", timeout=20)
    return _handle_response(response)


def enrich_request(request_id: str) -> Dict[str, Any]:
    """
    Trigger AI enrichment for a request.
    Adjust endpoint if your route is different.
    """
    response = requests.post(f"{BASE_URL}/requests/{request_id}/enrich", timeout=30)
    return _handle_response(response)


def submit_request(request_id: str) -> Dict[str, Any]:
    """
    Submit a request into the approval workflow so that
    the approval chain gets created.
    """
    response = requests.post(
        f"{BASE_URL}/requests/{request_id}/submit",
        json={"request_id": request_id},
        timeout=20
    )
    return _handle_response(response)


def approve_request(request_id: str, actor_name: str, actor_role: str):
    response = requests.post(
        f"{BASE_URL}/requests/{request_id}/approve",
        json={
            "request_id": request_id,
            "actor_name": actor_name,
            "actor_role": actor_role
        },
        timeout=20
    )
    return _handle_response(response)


def reject_request(request_id: str, actor_name: str, actor_role: str, reason: str):
    response = requests.post(
        f"{BASE_URL}/requests/{request_id}/reject",
        json={
            "request_id": request_id,
            "actor_name": actor_name,
            "actor_role": actor_role,
            "reason": reason
        },
        timeout=20
    )
    return _handle_response(response)

def get_audit_logs(request_id: str):
    response = requests.get(
        f"{BASE_URL}/requests/{request_id}/audit",
        timeout=20
    )
    return _handle_response(response)
        
    
