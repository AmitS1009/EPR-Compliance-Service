from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_submit_rejects_negative_quantity():
    response = client.post(
        "/submit",
        json={
            "producer_id": "GREENPACK-001",
            "month": "2026-04",
            "declared_quantities_kg": {
                "rigid_plastic": 12000,
                "flexible_plastic": -1,
                "multilayer_plastic": 3200,
            },
        },
    )
    assert response.status_code == 422


def test_submit_and_summary_sequence():
    submit_response = client.post(
        "/submit",
        json={
            "producer_id": "GREENPACK-001",
            "month": "2026-04",
            "declared_quantities_kg": {
                "rigid_plastic": 12000,
                "flexible_plastic": 8500,
                "multilayer_plastic": 3200,
            },
        },
    )
    assert submit_response.status_code == 200
    assert submit_response.json()["record_id"]

    summary_response = client.get("/summary/GREENPACK-001/2026-04")
    assert summary_response.status_code == 200
    body = summary_response.json()
    assert body["producer_id"] == "GREENPACK-001"
    flagged = [item for item in body["reconciliation"] if item["flagged"]]
    assert [item["category"] for item in flagged] == ["flexible_plastic"]
    assert body["narrative"]


def test_ask_unknown_returns_no_citations():
    response = client.post(
        "/ask",
        json={"question": "What is the corporate tax rate for GreenPack this year?"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "I do not know based on the provided documents"
    assert body["citations"] == []
