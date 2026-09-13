"""Real Strands agent: model chooses and invokes narrow operational tools."""
import os
from strands import Agent, tool
from strands.models.openai import OpenAIModel
from . import db
from .store import Operations

SYSTEM_PROMPT = """You are NeighborOps, an operations coordination agent for Karachi Community Pantry.
Automate routine, reversible coordination. Escalate human judgment. Use tools to inspect each request and current state.
Never fabricate missing information. Never reserve below the safety threshold, more than is available, or assign unavailable volunteers.
If location is missing, call mark_needs_information. If a threshold would be crossed, call request_human_approval.
For safe requests, classify, verify inventory, reserve, match a suitable volunteer, create a delivery task, and complete routine processing.
Do not claim success unless tools confirm it. A final text response does not change operational state.
Humans retain final authority over high-impact allocation. Handle only the request ID supplied in the user instruction."""

def build_tools(ops, target_id=None):
    def only_target(request_id):
        if target_id is not None and request_id != target_id:
            raise ValueError("Tool call is outside the claimed request")
    @tool
    def get_pending_requests() -> list:
        """List request IDs still marked NEW."""
        return [{"id": r["id"], "description": r["description"]} for r in ops.list(db.requests, db.requests.c.status == "NEW")]

    @tool
    def get_request_details(request_id: str) -> dict:
        """Inspect a request's description, location, category, requested quantity, and status."""
        only_target(request_id)
        r = ops.get(db.requests, request_id)
        if not r:
            raise ValueError("Request not found")
        return {k: r[k] for k in ("id", "description", "location", "category", "urgency", "status", "household_size", "structured_data")}

    @tool
    def classify_request(request_id: str, category: str, urgency: str, quantity: int, summary: str) -> dict:
        """Classify one request and record a concise reasoning summary. Category: FOOD/BABY/MEDICINE/GENERAL; urgency: LOW/NORMAL/HIGH."""
        only_target(request_id)
        return ops.classify(request_id, category, urgency, quantity, summary)

    @tool
    def get_inventory() -> list:
        """List current resource quantities and protected safety thresholds."""
        return [{k: r[k] for k in ("id", "name", "type", "available_quantity", "safety_threshold")} for r in ops.list(db.resources)]

    @tool
    def get_resource(resource_id: str) -> dict:
        """Inspect one resource by ID."""
        r = ops.get(db.resources, resource_id)
        if not r:
            raise ValueError("Resource not found")
        return {k: r[k] for k in ("id", "name", "type", "available_quantity", "safety_threshold")}

    @tool
    def check_safety_threshold(request_id: str, resource_id: str, requested_quantity: int) -> dict:
        """Check whether a proposed allocation leaves protected stock intact."""
        only_target(request_id)
        return ops.check_threshold(resource_id, requested_quantity, request_id)

    @tool
    def reserve_inventory(request_id: str, resource_id: str, quantity: int) -> dict:
        """Atomically reserve safe inventory; rejects threshold breaches and duplicate allocations."""
        only_target(request_id)
        return ops.reserve(request_id, resource_id, quantity)

    @tool
    def get_available_volunteers() -> list:
        """List volunteers who are currently available with their skills and workload."""
        return [{k: v[k] for k in ("id", "name", "transport_type", "max_capacity", "skills", "current_load")} for v in ops.list(db.volunteers, db.volunteers.c.availability == True)]

    @tool
    def match_volunteer(request_id: str) -> dict:
        """Find the lowest-load available volunteer whose skills fit a request."""
        only_target(request_id)
        return ops.match_volunteer(request_id) or {"status": "NO_MATCH"}

    @tool
    def create_delivery_task(request_id: str, volunteer_id: str) -> dict:
        """Assign an available, suitable volunteer to an allocated request."""
        only_target(request_id)
        return ops.create_task(request_id, volunteer_id)

    @tool
    def schedule_followup(request_id: str, reason: str, delay_hours: int) -> dict:
        """Schedule a follow-up task 1–720 hours from now."""
        only_target(request_id)
        return ops.followup(request_id, reason, delay_hours)

    @tool
    def draft_notification(request_id: str, event_type: str) -> dict:
        """Draft, but do not send, a status update for APPROVED, NEEDS_INFORMATION, or SCHEDULED."""
        only_target(request_id)
        return ops.notification(request_id, event_type)

    @tool
    def request_human_approval(request_id: str, reason: str) -> dict:
        """Escalate a safety, fairness, or vulnerable-beneficiary judgment to a human."""
        only_target(request_id)
        return ops.human_review(request_id, reason)

    @tool
    def mark_needs_information(request_id: str, missing_fields: list[str]) -> dict:
        """Mark a request pending critical missing fields: location, contact, or household_size."""
        only_target(request_id)
        return ops.needs_information(request_id, missing_fields)

    @tool
    def complete_routine_processing(request_id: str) -> dict:
        """Mark a safely allocated request as coordinated; refuses without an allocation."""
        only_target(request_id)
        return ops.complete_routine(request_id)

    return [get_pending_requests, get_request_details, classify_request, get_inventory, get_resource,
        check_safety_threshold, reserve_inventory, get_available_volunteers, match_volunteer,
        create_delivery_task, schedule_followup, draft_notification, request_human_approval,
        mark_needs_information, complete_routine_processing]

def model_ids():
    primary = os.getenv("OPENROUTER_MODEL", "nex-agi/nex-n2-pro:free")
    fallback = os.getenv("OPENROUTER_FALLBACK_MODEL", "openrouter/free")
    return list(dict.fromkeys([primary, fallback]))

def process_request(ops, request_id):
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("Agent temporarily unavailable — configure OPENROUTER_API_KEY and retry.")
    last_error = None
    for model_id in model_ids():
        if model_id != "openrouter/free" and not model_id.endswith(":free"):
            raise ValueError("Only free OpenRouter models are allowed")
        try:
            model = OpenAIModel(client_args={"api_key": key, "base_url": "https://openrouter.ai/api/v1", "timeout": 45.0},
                model_id=model_id, params={"max_tokens": 1800, "temperature": 0})
            # Strands' default callback prints model text. Keep beneficiary content and
            # provider output out of process logs (and avoid Windows console encoding errors).
            agent = Agent(model=model, tools=build_tools(ops, request_id),
                system_prompt=SYSTEM_PROMPT, callback_handler=None)
            agent(f"Process request {request_id}. Inspect it and current stock first. Call tools for every actual action. Stop after this request.")
            return model_id
        except Exception as exc:
            # Never log exception text: some providers embed request headers in errors.
            last_error = exc
    raise RuntimeError("Agent temporarily unavailable — operational data is safe. Retry agent run.") from last_error
