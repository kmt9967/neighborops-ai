import os
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, insert, select, update
from . import db
from .agent import process_request
from .store import ORG, Operations, event, seed

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
engine = db.make_engine()
db.init_db(engine)
seed(engine)
app = FastAPI(title="NeighborOps AI API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=[x.strip() for x in os.getenv("FRONTEND_ORIGINS", "http://localhost:3000").split(",")],
    allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

def safe(v):
    if isinstance(v, datetime):
        return v.isoformat()
    if isinstance(v, list):
        return [safe(x) for x in v]
    if isinstance(v, dict):
        return {k: safe(x) for k, x in v.items()}
    return v

def ops():
    return Operations(engine)

@app.get("/api/health")
def health():
    return {"status": "ok", "agent_configured": bool(os.getenv("OPENROUTER_API_KEY"))}

@app.get("/api/dashboard")
def dashboard():
    o = ops()
    reqs = o.list(db.requests)
    return safe({"organization": "Karachi Community Pantry", "open_requests": sum(r["status"] not in ("COMPLETED", "REJECTED") for r in reqs),
        "pending_requests": sum(r["status"] == "NEW" for r in reqs),
        "auto_handled": sum(r["status"] in ("AUTO_APPROVED", "ALLOCATED", "SCHEDULED") for r in reqs),
        "human_review": sum(r["status"] == "HUMAN_REVIEW" for r in reqs),
        "available_volunteers": len(o.list(db.volunteers, db.volunteers.c.availability == True)),
        "resources": o.list(db.resources), "recent_requests": reqs[:5],
        "recent_events": sorted(o.list(db.agent_events), key=lambda e: e["created_at"], reverse=True)[:8]})

@app.get("/api/requests")
def list_requests(status: str | None = None):
    condition = db.requests.c.status == status if status else None
    return safe(ops().list(db.requests, condition))

@app.get("/api/requests/{request_id}")
def request_details(request_id: str):
    try:
        return safe(ops().details(request_id))
    except ValueError:
        raise HTTPException(404, "Request not found")

@app.get("/api/resources")
def list_resources():
    return safe(ops().list(db.resources))

@app.get("/api/volunteers")
def list_volunteers():
    return safe(ops().list(db.volunteers))

@app.get("/api/activity")
def activity():
    return safe(sorted(ops().list(db.agent_events, limit=300), key=lambda e: e["created_at"], reverse=True))

@app.post("/api/agent/run")
def run_agent():
    run_id = db.uid()
    with engine.begin() as c:
        c.execute(insert(db.agent_runs).values(id=run_id, organization_id=ORG, status="RUNNING", started_at=db.now(), requests_processed=0))
        event(c, "AGENT_RUN_STARTED", "Agent run started", run_id=run_id)
    summary = {"run_id": run_id, "processed": 0, "auto_handled": 0, "human_review": 0, "needs_information": 0, "failed": 0}
    if not os.getenv("OPENROUTER_API_KEY"):
        with engine.begin() as c:
            c.execute(update(db.agent_runs).where(db.agent_runs.c.id == run_id).values(status="FAILED", completed_at=db.now(), error_message="Agent key not configured"))
            event(c, "AGENT_UNAVAILABLE", "Agent temporarily unavailable — operational data is safe. Retry agent run.", run_id=run_id)
        raise HTTPException(503, {**summary, "message": "Agent temporarily unavailable — operational data is safe. Retry agent run."})
    model_used = None
    for request in ops().list(db.requests, db.requests.c.status == "NEW"):
        request_id = request["id"]
        # Atomic claim prevents two concurrent runs from processing the same request.
        with engine.begin() as c:
            claimed = c.execute(update(db.requests).where(and_(db.requests.c.id == request_id,
                db.requests.c.status == "NEW")).values(status="PROCESSING", updated_at=db.now()))
            if claimed.rowcount != 1:
                continue
            event(c, "PROCESSING", "Agent inspecting request", request_id, run_id)
        try:
            model_used = process_request(Operations(engine, run_id), request_id)
            state = ops().get(db.requests, request_id)["status"]
            if state == "PROCESSING":
                raise RuntimeError("Agent did not complete the required operational workflow")
            summary["processed"] += 1
            if state in ("AUTO_APPROVED", "ALLOCATED", "SCHEDULED"):
                summary["auto_handled"] += 1
            elif state == "HUMAN_REVIEW":
                summary["human_review"] += 1
            elif state == "NEEDS_INFORMATION":
                summary["needs_information"] += 1
        except Exception:
            summary["failed"] += 1
            with engine.begin() as c:
                current = db.row(c.execute(select(db.requests).where(db.requests.c.id == request_id)).first())
                # Failed inference can be retried; completed tool mutations remain auditable and idempotent.
                if current["status"] == "PROCESSING":
                    c.execute(update(db.requests).where(db.requests.c.id == request_id).values(status="NEW", updated_at=db.now()))
                event(c, "AGENT_ERROR", "Agent temporarily unavailable for this request; retry safely.", request_id, run_id)
    with engine.begin() as c:
        c.execute(update(db.agent_runs).where(db.agent_runs.c.id == run_id).values(
            status="COMPLETED" if not summary["failed"] else "PARTIAL", completed_at=db.now(),
            model_used=model_used, requests_processed=summary["processed"],
            error_message="One or more requests could not be processed" if summary["failed"] else None))
        event(c, "AGENT_RUN_FINISHED", f"Agent run finished · {summary['processed']} processed, {summary['failed']} failed", run_id=run_id)
    return summary

class Decision(BaseModel):
    decision: str
    quantity: int | None = Field(default=None, ge=1, le=100)
    notes: str = Field(default="", max_length=1000)

@app.post("/api/requests/{request_id}/decision")
def decide(request_id: str, body: Decision):
    o = ops()
    r = o.get(db.requests, request_id)
    if not r:
        raise HTTPException(404, "Request not found")
    if r["status"] != "HUMAN_REVIEW":
        raise HTTPException(409, "Request is not awaiting human review")
    if body.decision not in ("APPROVE_FULL", "REDUCE_ALLOCATION", "REJECT"):
        raise HTTPException(422, "Invalid decision")
    requested = (r["structured_data"] or {}).get("requested_quantity", 1)
    quantity = requested if body.decision == "APPROVE_FULL" else body.quantity
    if body.decision == "REDUCE_ALLOCATION" and (not quantity or quantity >= requested):
        raise HTTPException(422, "Reduced quantity must be below requested quantity")
    resource = next((x for x in o.list(db.resources) if x["type"] == r["category"]), None)
    if body.decision != "REJECT" and (not resource or quantity > resource["available_quantity"]):
        raise HTTPException(409, "Insufficient available inventory")
    with engine.begin() as c:
        decision = db.row(c.execute(select(db.human_decisions).where(db.human_decisions.c.request_id == request_id).order_by(desc(db.human_decisions.c.created_at))).first())
        if decision:
            c.execute(update(db.human_decisions).where(db.human_decisions.c.id == decision["id"]).values(
                selected_option=body.decision, decision_notes=body.notes, decided_at=db.now()))
        c.execute(update(db.requests).where(db.requests.c.id == request_id).values(
            status="REJECTED" if body.decision == "REJECT" else "APPROVED", updated_at=db.now()))
        event(c, "HUMAN_DECISION", f"Operator chose {body.decision.replace('_', ' ').lower()}" + (f" · {quantity} units" if quantity else ""), request_id,
            metadata={"decision": body.decision, "quantity": quantity, "notes": body.notes})
    if body.decision != "REJECT":
        try:
            o.reserve(request_id, resource["id"], quantity, human_override=True)
            match = o.match_volunteer(request_id)
            if match:
                o.create_task(request_id, match["id"])
        except ValueError as exc:
            raise HTTPException(409, str(exc))
    return safe(o.details(request_id))
