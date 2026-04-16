from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_full_procurement_flow():
    create_resp = client.post(
        "/requests",
        json={
            "title": "Purchase new laptops",
            "description": "Need to buy 15 laptops for engineering team",
            "created_by": "Avantika",
            "request_type": "PROCUREMENT",
            "amount": 25000,
        },
    )
    assert create_resp.status_code == 200
    request_id = create_resp.json()["id"]

    submit_resp = client.post(f"/requests/{request_id}/submit")
    assert submit_resp.status_code == 200
    assert submit_resp.json()["state"] == "IN_REVIEW"

    approve_1 = client.post(
        f"/requests/{request_id}/approve",
        json={"actor_name": "Manager A", "actor_role": "MANAGER", "comments": "Looks fine"},
    )
    assert approve_1.status_code == 200
    assert approve_1.json()["current_required_role"] == "FINANCE"

    approve_2 = client.post(
        f"/requests/{request_id}/approve",
        json={"actor_name": "Finance A", "actor_role": "FINANCE", "comments": "Budget available"},
    )
    assert approve_2.status_code == 200
    assert approve_2.json()["current_required_role"] == "DIRECTOR"

    approve_3 = client.post(
        f"/requests/{request_id}/approve",
        json={"actor_name": "Director A", "actor_role": "DIRECTOR", "comments": "Approved"},
    )
    assert approve_3.status_code == 200
    assert approve_3.json()["state"] == "APPROVED"
