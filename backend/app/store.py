"""Policy-enforcing operations. Every mutation is transactional and audit logged."""
from datetime import timedelta
from sqlalchemy import and_, insert, select, update
from . import db

ORG = "11111111-1111-4111-8111-111111111111"

def event(conn, kind, message, request_id=None, run_id=None, metadata=None):
    conn.execute(insert(db.agent_events).values(id=db.uid(), event_type=kind, message=message,
        request_id=request_id, agent_run_id=run_id, metadata=metadata or {}, created_at=db.now()))

def seed(engine):
    with engine.begin() as c:
        if c.execute(select(db.organizations.c.id).limit(1)).first():
            return
        c.execute(insert(db.organizations).values(id=ORG, name="Karachi Community Pantry"))
        for id_, name, typ, total, available, threshold in [
            ("food", "Food Box", "FOOD", 24, 18, 8),
            ("baby", "Baby Care Kit", "BABY", 10, 7, 3),
            ("medicine", "Medicine Support Voucher", "MEDICINE", 8, 4, 2),
        ]:
            c.execute(insert(db.resources).values(id=id_, organization_id=ORG, name=name, type=typ,
                total_quantity=total, available_quantity=available, reserved_quantity=total-available,
                safety_threshold=threshold, updated_at=db.now()))
        for id_, name, transport, available, capacity, skills, load in [
            ("ahmed", "Ahmed Khan", "car", True, "medium", ["food", "general", "delivery"], 0),
            ("sara", "Sara Ali", "motorcycle", True, "small", ["baby", "food", "delivery"], 1),
            ("hassan", "Hassan Raza", "car", False, "medium", ["food", "delivery"], 0),
        ]:
            c.execute(insert(db.volunteers).values(id=id_, organization_id=ORG, name=name,
                transport_type=transport, availability=available, max_capacity=capacity,
                skills=skills, current_load=load, created_at=db.now()))
        for id_, name, desc, household, location, category, qty in [
            ("req-001", "Mariam Qureshi", "Family of six needs food assistance this week.", 6, "Gulshan-e-Iqbal, Karachi", "FOOD", 2),
            ("req-002", "Nadia Farooq", "Elderly woman needs food delivered because she cannot travel.", 1, "North Nazimabad, Karachi", "FOOD", 1),
            ("req-003", "Hina Siddiqui", "Single mother requests a baby-care kit.", 2, "Clifton, Karachi", "BABY", 1),
            ("req-004", "Community Event Team", "Organization requests 10 food boxes for a community event.", None, "Saddar, Karachi", "FOOD", 10),
            ("req-005", "Bilal Ahmed", "Family requests assistance but has no usable address or location.", 4, None, "FOOD", 1),
        ]:
            c.execute(insert(db.requests).values(id=id_, organization_id=ORG, requester_name=name,
                category=category, description=desc, household_size=household, location=location,
                urgency="NORMAL", status="NEW", structured_data={"requested_quantity": qty,
                "delivery_required": id_ in ("req-002", "req-005")}, created_at=db.now(), updated_at=db.now()))
            event(c, "REQUEST_RECEIVED", f"New request received from {name}", id_)

class Operations:
    def __init__(self, engine, run_id=None):
        self.engine, self.run_id = engine, run_id

    def list(self, table, condition=None, limit=100):
        with self.engine.connect() as c:
            q = select(table).limit(limit)
            if condition is not None:
                q = q.where(condition)
            if table.c.get("created_at") is not None:
                q = q.order_by(table.c.created_at, table.c.id)
            return [db.row(r) for r in c.execute(q)]

    def get(self, table, id_):
        with self.engine.connect() as c:
            return db.row(c.execute(select(table).where(table.c.id == id_)).first())

    def details(self, request_id):
        request = self.get(db.requests, request_id)
        if not request:
            raise ValueError("Request not found")
        request["allocations"] = self.list(db.allocations, db.allocations.c.request_id == request_id)
        request["events"] = self.list(db.agent_events, db.agent_events.c.request_id == request_id)
        request["decisions"] = self.list(db.human_decisions, db.human_decisions.c.request_id == request_id)
        request["tasks"] = self.list(db.tasks, db.tasks.c.request_id == request_id)
        return request

    def classify(self, request_id, category, urgency, quantity, summary):
        if category not in ("FOOD", "BABY", "MEDICINE", "GENERAL") or urgency not in ("LOW", "NORMAL", "HIGH"):
            raise ValueError("Invalid category or urgency")
        if not 1 <= quantity <= 100 or len(summary) > 800:
            raise ValueError("Invalid quantity or summary")
        with self.engine.begin() as c:
            r = db.row(c.execute(select(db.requests).where(db.requests.c.id == request_id)).first())
            if not r or r["status"] not in ("NEW", "PROCESSING"):
                raise ValueError("Request not actionable")
            data = {**(r["structured_data"] or {}), "requested_quantity": quantity}
            c.execute(update(db.requests).where(db.requests.c.id == request_id).values(
                category=category, urgency=urgency, structured_data=data, reasoning_summary=summary,
                status="PROCESSING", updated_at=db.now()))
            event(c, "CLASSIFIED", f"Classified as {category.lower()} assistance · {urgency.lower()} urgency", request_id, self.run_id)
        return {"category": category, "quantity": quantity, "status": "PROCESSING"}

    def check_threshold(self, resource_id, quantity, request_id=None):
        r = self.get(db.resources, resource_id)
        if not r or quantity < 1:
            raise ValueError("Invalid resource or quantity")
        remaining = r["available_quantity"] - quantity
        result = {"resource": r["name"], "available": r["available_quantity"],
            "threshold": r["safety_threshold"], "remaining": remaining,
            "safe": remaining > r["safety_threshold"]}
        if request_id:
            with self.engine.begin() as c:
                event(c, "SAFETY_CHECK", f"{r['name']} checked: {quantity} requested, {remaining} would remain; " +
                    ("protected reserve preserved" if result["safe"] else "human decision required"), request_id, self.run_id, result)
        return result

    def reserve(self, request_id, resource_id, quantity, human_override=False):
        if quantity < 1 or quantity > 100:
            raise ValueError("Quantity must be between 1 and 100")
        with self.engine.begin() as c:
            r = db.row(c.execute(select(db.requests).where(db.requests.c.id == request_id)).first())
            resource = db.row(c.execute(select(db.resources).where(db.resources.c.id == resource_id)).first())
            if not r or not resource:
                raise ValueError("Request or resource not found")
            if r["category"] != resource["type"]:
                raise ValueError("Resource category mismatch")
            if not r["location"]:
                raise ValueError("Missing location")
            existing = c.execute(select(db.allocations).where(and_(db.allocations.c.request_id == request_id,
                db.allocations.c.resource_id == resource_id))).first()
            if existing:
                return {"status": "ALREADY_RESERVED", "quantity": existing._mapping["quantity"]}
            if r["status"] not in ("PROCESSING", "NEW", "HUMAN_REVIEW", "APPROVED"):
                raise ValueError("Request not eligible for allocation")
            floor = 0 if human_override else resource["safety_threshold"]
            result = c.execute(update(db.resources).where(and_(db.resources.c.id == resource_id,
                db.resources.c.available_quantity >= quantity + floor + (0 if human_override else 1))).values(
                available_quantity=db.resources.c.available_quantity - quantity,
                reserved_quantity=db.resources.c.reserved_quantity + quantity, updated_at=db.now()))
            if result.rowcount != 1:
                raise ValueError("HUMAN_REVIEW_REQUIRED" if resource["available_quantity"] >= quantity else "INSUFFICIENT_INVENTORY")
            c.execute(insert(db.allocations).values(id=db.uid(), request_id=request_id, resource_id=resource_id,
                quantity=quantity, status="RESERVED", created_at=db.now()))
            c.execute(update(db.requests).where(db.requests.c.id == request_id).values(status="ALLOCATED", updated_at=db.now()))
            event(c, "INVENTORY_RESERVED", f"Reserved {quantity} units of {resource['name']}", request_id, self.run_id,
                {"quantity": quantity, "resource_id": resource_id, "human_override": human_override})
            return {"status": "RESERVED", "quantity": quantity}

    def needs_information(self, request_id, fields):
        allowed = {"location", "contact", "household_size"}
        if not fields or set(fields) - allowed:
            raise ValueError("Invalid missing fields")
        with self.engine.begin() as c:
            c.execute(update(db.requests).where(db.requests.c.id == request_id).values(status="NEEDS_INFORMATION", updated_at=db.now()))
            event(c, "NEEDS_INFORMATION", f"Needs information: {', '.join(fields)}", request_id, self.run_id, {"missing_fields": fields})
        return {"status": "NEEDS_INFORMATION"}

    def human_review(self, request_id, reason):
        if not reason or len(reason) > 1000:
            raise ValueError("A concise reason is required")
        with self.engine.begin() as c:
            r = db.row(c.execute(select(db.requests).where(db.requests.c.id == request_id)).first())
            if not r or r["status"] not in ("NEW", "PROCESSING"):
                raise ValueError("Request not eligible for review")
            c.execute(update(db.requests).where(db.requests.c.id == request_id).values(status="HUMAN_REVIEW", reasoning_summary=reason, updated_at=db.now()))
            c.execute(insert(db.human_decisions).values(id=db.uid(), request_id=request_id, reason=reason,
                recommended_option="REDUCE_ALLOCATION", available_options=["APPROVE_FULL", "REDUCE_ALLOCATION", "REJECT"], created_at=db.now()))
            event(c, "HUMAN_DECISION_REQUIRED", reason, request_id, self.run_id)
        return {"status": "HUMAN_REVIEW"}

    def match_volunteer(self, request_id):
        r = self.get(db.requests, request_id)
        if not r or not r["location"]:
            raise ValueError("Location required")
        allocated = self.list(db.allocations, db.allocations.c.request_id == request_id)
        quantity = allocated[0]["quantity"] if allocated else (r["structured_data"] or {}).get("requested_quantity", 1)
        capacity = {"small": 2, "medium": 6, "large": 20}
        candidates = [v for v in self.list(db.volunteers) if v["availability"] and
            r["category"].lower() in v["skills"] and "delivery" in v["skills"] and
            quantity <= capacity.get(v["max_capacity"], 0)]
        candidates.sort(key=lambda v: (v["current_load"], v["name"]))
        return candidates[0] if candidates else None

    def create_task(self, request_id, volunteer_id):
        with self.engine.begin() as c:
            r = db.row(c.execute(select(db.requests).where(db.requests.c.id == request_id)).first())
            v = db.row(c.execute(select(db.volunteers).where(db.volunteers.c.id == volunteer_id)).first())
            a = c.execute(select(db.allocations).where(db.allocations.c.request_id == request_id)).first()
            capacity = {"small": 2, "medium": 6, "large": 20}
            if not r or not r["location"] or not a or not v or not v["availability"] or r["category"].lower() not in v["skills"] or a._mapping["quantity"] > capacity.get(v["max_capacity"], 0):
                raise ValueError("Unavailable or unsuitable volunteer, missing location, or no allocation")
            existing = c.execute(select(db.tasks).where(db.tasks.c.request_id == request_id)).first()
            if existing:
                return {"status": "ALREADY_SCHEDULED"}
            c.execute(insert(db.tasks).values(id=db.uid(), request_id=request_id, volunteer_id=volunteer_id,
                type="DELIVERY", status="SCHEDULED", created_at=db.now()))
            c.execute(update(db.allocations).where(db.allocations.c.request_id == request_id).values(volunteer_id=volunteer_id))
            c.execute(update(db.volunteers).where(db.volunteers.c.id == volunteer_id).values(current_load=db.volunteers.c.current_load + 1))
            c.execute(update(db.requests).where(db.requests.c.id == request_id).values(status="SCHEDULED", updated_at=db.now()))
            event(c, "VOLUNTEER_MATCHED", f"{v['name']} matched for delivery", request_id, self.run_id)
            event(c, "TASK_CREATED", "Delivery task scheduled", request_id, self.run_id)
        return {"status": "SCHEDULED", "volunteer": v["name"]}

    def complete_routine(self, request_id):
        with self.engine.begin() as c:
            r = db.row(c.execute(select(db.requests).where(db.requests.c.id == request_id)).first())
            a = c.execute(select(db.allocations).where(db.allocations.c.request_id == request_id)).first()
            if not r or not a or r["status"] not in ("ALLOCATED", "SCHEDULED"):
                raise ValueError("An allocation is required before completion")
            if (r["structured_data"] or {}).get("delivery_required") and not c.execute(select(db.tasks).where(db.tasks.c.request_id == request_id)).first():
                raise ValueError("A delivery volunteer must be scheduled before completion")
            c.execute(update(db.requests).where(db.requests.c.id == request_id).values(status="AUTO_APPROVED", updated_at=db.now()))
            event(c, "ROUTINE_COORDINATED", "Routine coordination completed automatically", request_id, self.run_id)
        return {"status": "AUTO_APPROVED"}

    def followup(self, request_id, reason, delay_hours):
        if not 1 <= delay_hours <= 720 or not reason or len(reason) > 400:
            raise ValueError("Invalid follow-up")
        with self.engine.begin() as c:
            existing = c.execute(select(db.tasks).where(db.tasks.c.request_id == request_id)).first()
            if existing:
                return {"status": "TASK_EXISTS"}
            c.execute(insert(db.tasks).values(id=db.uid(), request_id=request_id, type="FOLLOWUP", status="SCHEDULED",
                due_at=db.now() + timedelta(hours=delay_hours), created_at=db.now()))
            event(c, "FOLLOWUP_SCHEDULED", reason, request_id, self.run_id)
        return {"status": "SCHEDULED"}

    def notification(self, request_id, event_type):
        r = self.get(db.requests, request_id)
        if not r or event_type not in ("APPROVED", "NEEDS_INFORMATION", "SCHEDULED"):
            raise ValueError("Invalid notification")
        draft = f"Hello {r['requester_name']}, your assistance request is {event_type.lower().replace('_', ' ')}. Karachi Community Pantry will follow up."
        with self.engine.begin() as c:
            c.execute(insert(db.notifications).values(id=db.uid(), request_id=request_id, event_type=event_type, draft=draft, created_at=db.now()))
            event(c, "NOTIFICATION_DRAFTED", "Status update drafted for coordinator review", request_id, self.run_id)
        return {"draft": draft, "sent": False}
