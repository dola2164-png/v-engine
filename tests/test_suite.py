import pytest
from fastapi.testclient import TestClient
from bot import app
from engine.context_store import store

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_teardown():
    store.teardown()
    yield
    store.teardown()

def test_healthz():
    resp = client.get("/v1/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "contexts_loaded" in data

def test_metadata():
    resp = client.get("/v1/metadata")
    assert resp.status_code == 200
    data = resp.json()
    assert "team_name" in data
    assert "model" in data

def test_context_push_and_idempotency():
    payload = {
        "scope": "category",
        "context_id": "dentists",
        "version": 2,
        "payload": {"slug": "dentists"},
        "delivered_at": "2026-04-26T10:00:00Z"
    }
    # Version 2 push -> 200 OK
    resp = client.post("/v1/context", json=payload)
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True

    # Same version (v2) re-push -> 200 OK (idempotent no-op)
    resp = client.post("/v1/context", json=payload)
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True

    # Stale version (v1 < v2) push -> 409 Conflict
    stale_payload = {
        "scope": "category",
        "context_id": "dentists",
        "version": 1,
        "payload": {"slug": "dentists"},
        "delivered_at": "2026-04-26T10:00:00Z"
    }
    resp = client.post("/v1/context", json=stale_payload)
    assert resp.status_code == 409
    assert resp.json()["accepted"] is False

    # Higher version (v3 > v2) push -> 200 OK
    payload["version"] = 3
    resp = client.post("/v1/context", json=payload)
    assert resp.status_code == 200
    assert resp.json()["accepted"] is True

def test_auto_reply_handling():
    conv_id = "conv_test_auto"
    msg = "Thank you for contacting us! Our team will respond shortly."
    resp = client.post("/v1/reply", json={
        "conversation_id": conv_id,
        "from_role": "merchant",
        "message": msg,
        "received_at": "2026-04-26T10:00:00Z",
        "turn_number": 1
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] in ["wait", "end"]

def test_intent_transition():
    conv_id = "conv_test_intent"
    msg = "Ok lets do it. Whats next?"
    resp = client.post("/v1/reply", json={
        "conversation_id": conv_id,
        "from_role": "merchant",
        "message": msg,
        "received_at": "2026-04-26T10:00:00Z",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "send"
    body_lower = data["body"].lower()
    assert any(w in body_lower for w in ["done", "sending", "draft", "here", "confirm", "proceed", "next"])
    assert not any(w in body_lower for w in ["would you", "do you", "can you tell", "what if", "how about"])

def test_hostile_exit():
    conv_id = "conv_test_hostile"
    msg = "Stop messaging me. This is useless spam."
    resp = client.post("/v1/reply", json={
        "conversation_id": conv_id,
        "from_role": "merchant",
        "message": msg,
        "received_at": "2026-04-26T10:00:00Z",
        "turn_number": 2
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["action"] == "end"
