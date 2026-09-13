"""Transactional operational store. SQLite is local-only; DATABASE_URL accepts Supabase Postgres."""
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, MetaData, String, Table, Text, UniqueConstraint, create_engine
from sqlalchemy.engine import make_url

metadata = MetaData()

def uid():
    return str(uuid4())

def now():
    return datetime.now(timezone.utc)

organizations = Table("organizations", metadata,
    Column("id", String(36), primary_key=True), Column("name", String(200), nullable=False))
requests = Table("requests", metadata,
    Column("id", String(36), primary_key=True), Column("organization_id", String(36), ForeignKey("organizations.id"), nullable=False),
    Column("requester_name", String(160), nullable=False), Column("requester_contact", String(160)),
    Column("category", String(60), nullable=False, default="UNCLASSIFIED"), Column("description", Text, nullable=False),
    Column("household_size", Integer), Column("location", String(300)), Column("urgency", String(20), nullable=False, default="NORMAL"),
    Column("status", String(30), nullable=False, default="NEW"), Column("structured_data", JSON, nullable=False, default=dict),
    Column("reasoning_summary", Text), Column("created_at", DateTime(timezone=True), nullable=False, default=now),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=now))
resources = Table("resources", metadata,
    Column("id", String(36), primary_key=True), Column("organization_id", String(36), ForeignKey("organizations.id"), nullable=False),
    Column("name", String(160), nullable=False), Column("type", String(60), nullable=False),
    Column("total_quantity", Integer, nullable=False), Column("available_quantity", Integer, nullable=False),
    Column("reserved_quantity", Integer, nullable=False), Column("safety_threshold", Integer, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False, default=now))
volunteers = Table("volunteers", metadata,
    Column("id", String(36), primary_key=True), Column("organization_id", String(36), ForeignKey("organizations.id"), nullable=False),
    Column("name", String(160), nullable=False), Column("transport_type", String(30), nullable=False),
    Column("availability", Boolean, nullable=False), Column("max_capacity", String(20), nullable=False),
    Column("skills", JSON, nullable=False), Column("current_load", Integer, nullable=False, default=0),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now))
allocations = Table("allocations", metadata,
    Column("id", String(36), primary_key=True), Column("request_id", String(36), ForeignKey("requests.id"), nullable=False),
    Column("resource_id", String(36), ForeignKey("resources.id"), nullable=False), Column("quantity", Integer, nullable=False),
    Column("volunteer_id", String(36), ForeignKey("volunteers.id")), Column("status", String(30), nullable=False, default="RESERVED"),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now), UniqueConstraint("request_id", "resource_id"))
agent_runs = Table("agent_runs", metadata,
    Column("id", String(36), primary_key=True), Column("organization_id", String(36), ForeignKey("organizations.id"), nullable=False),
    Column("status", String(20), nullable=False), Column("started_at", DateTime(timezone=True), nullable=False, default=now),
    Column("completed_at", DateTime(timezone=True)), Column("model_used", String(160)),
    Column("requests_processed", Integer, nullable=False, default=0), Column("error_message", Text))
agent_events = Table("agent_events", metadata,
    Column("id", String(36), primary_key=True), Column("agent_run_id", String(36), ForeignKey("agent_runs.id")),
    Column("request_id", String(36), ForeignKey("requests.id")), Column("event_type", String(60), nullable=False),
    Column("message", Text, nullable=False), Column("metadata", JSON, nullable=False, default=dict),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now))
human_decisions = Table("human_decisions", metadata,
    Column("id", String(36), primary_key=True), Column("request_id", String(36), ForeignKey("requests.id"), nullable=False),
    Column("reason", Text, nullable=False), Column("recommended_option", String(40)),
    Column("available_options", JSON, nullable=False), Column("selected_option", String(40)),
    Column("decision_notes", Text), Column("decided_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now))
tasks = Table("tasks", metadata,
    Column("id", String(36), primary_key=True), Column("request_id", String(36), ForeignKey("requests.id"), nullable=False, unique=True),
    Column("volunteer_id", String(36), ForeignKey("volunteers.id")), Column("type", String(40), nullable=False),
    Column("status", String(30), nullable=False), Column("due_at", DateTime(timezone=True)),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now))
notifications = Table("notifications", metadata,
    Column("id", String(36), primary_key=True), Column("request_id", String(36), ForeignKey("requests.id"), nullable=False),
    Column("event_type", String(40), nullable=False), Column("draft", Text, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False, default=now))

def make_engine(url=None):
    url = url or os.getenv("DATABASE_URL", "sqlite:///./neighborops.db")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    parsed = make_url(url)
    cert = parsed.query.get("sslrootcert")
    if cert and not Path(cert).is_absolute():
        # Resolve bundled CA files against backend/, independent of the process cwd.
        parsed = parsed.update_query_dict({"sslrootcert": str((Path(__file__).resolve().parents[1] / cert).resolve())})
    return create_engine(parsed, connect_args={"check_same_thread": False} if parsed.get_backend_name() == "sqlite" else {}, pool_pre_ping=True)

def init_db(engine):
    metadata.create_all(engine)

def row(result):
    return dict(result._mapping) if result else None
