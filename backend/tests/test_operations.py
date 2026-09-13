import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from app import db, main
from app.store import Operations, seed

@pytest.fixture
def setup(tmp_path, monkeypatch):
    engine = db.make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    db.init_db(engine)
    seed(engine)
    monkeypatch.setattr(main, "engine", engine)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    return Operations(engine), TestClient(main.app)

def test_seed_and_api(setup):
    ops, client = setup
    assert len(client.get("/api/requests").json()) == 5
    assert client.get("/api/dashboard").json()["pending_requests"] == 5
    assert len(client.get("/api/activity").json()) == 5

def test_safe_reservation_is_idempotent(setup):
    ops, _ = setup
    ops.classify("req-001", "FOOD", "NORMAL", 2, "Routine food request")
    assert ops.reserve("req-001", "food", 2)["status"] == "RESERVED"
    assert ops.reserve("req-001", "food", 2)["status"] == "ALREADY_RESERVED"
    assert ops.get(db.resources, "food")["available_quantity"] == 16
    assert len(ops.list(db.allocations)) == 1
    assert any(e["event_type"] == "INVENTORY_RESERVED" for e in ops.details("req-001")["events"])

def test_threshold_and_no_negative_inventory(setup):
    ops, _ = setup
    ops.classify("req-004", "FOOD", "NORMAL", 10, "Large event allocation")
    assert ops.check_threshold("food", 10)["safe"] is False  # reaching the protected floor requires review
    with pytest.raises(ValueError, match="HUMAN_REVIEW_REQUIRED"):
        ops.reserve("req-004", "food", 10)
    with pytest.raises(ValueError, match="HUMAN_REVIEW_REQUIRED"):
        ops.reserve("req-004", "food", 11)
    with pytest.raises(ValueError, match="INSUFFICIENT_INVENTORY"):
        ops.reserve("req-004", "food", 25)
    assert ops.get(db.resources, "food")["available_quantity"] == 18

def test_missing_location_and_unavailable_volunteer(setup):
    ops, _ = setup
    ops.classify("req-005", "FOOD", "NORMAL", 1, "Missing delivery location")
    ops.needs_information("req-005", ["location"])
    assert ops.get(db.requests, "req-005")["status"] == "NEEDS_INFORMATION"
    with pytest.raises(ValueError, match="Missing location"):
        ops.reserve("req-005", "food", 1)
    ops.classify("req-002", "FOOD", "NORMAL", 1, "Delivery required")
    ops.reserve("req-002", "food", 1)
    with pytest.raises(ValueError, match="delivery volunteer"):
        ops.complete_routine("req-002")
    with pytest.raises(ValueError, match="Unavailable"):
        ops.create_task("req-002", "hassan")
    assert ops.match_volunteer("req-002")["id"] == "ahmed"

def test_routine_completion_and_human_reduction(setup):
    ops, client = setup
    ops.classify("req-003", "BABY", "NORMAL", 1, "Baby care request")
    ops.reserve("req-003", "baby", 1)
    ops.create_task("req-003", "sara")
    ops.complete_routine("req-003")
    assert ops.get(db.requests, "req-003")["status"] == "AUTO_APPROVED"
    ops.classify("req-004", "FOOD", "NORMAL", 10, "Large event request")
    ops.human_review("req-004", "Would consume protected food reserve")
    response = client.post("/api/requests/req-004/decision", json={"decision":"REDUCE_ALLOCATION","quantity":4,"notes":"Protect reserve"})
    assert response.status_code == 200, response.text
    assert ops.get(db.resources, "food")["available_quantity"] == 14
    assert ops.details("req-004")["allocations"][0]["quantity"] == 4
    assert any(e["event_type"] == "HUMAN_DECISION" for e in ops.details("req-004")["events"])
    assert client.post("/api/requests/req-004/decision", json={"decision":"REDUCE_ALLOCATION","quantity":4}).status_code == 409

def test_no_key_fails_without_mutating_requests(setup):
    ops, client = setup
    response = client.post("/api/agent/run")
    assert response.status_code == 503
    assert all(r["status"] == "NEW" for r in ops.list(db.requests))
    assert any(e["event_type"] == "AGENT_UNAVAILABLE" for e in ops.list(db.agent_events))

def test_model_error_releases_claim_safely(setup, monkeypatch):
    ops, client = setup
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-only-placeholder")
    monkeypatch.setattr(main, "process_request", lambda *_: (_ for _ in ()).throw(RuntimeError("provider down")))
    result = client.post("/api/agent/run")
    assert result.status_code == 200
    assert result.json()["failed"] == 5
    assert all(r["status"] == "NEW" for r in ops.list(db.requests))
    assert ops.get(db.resources, "food")["available_quantity"] == 18
