"""Idempotent fictional seed data. Run after applying schema or let the API seed at startup."""
from app.db import init_db, make_engine
from app.store import seed
engine = make_engine()
init_db(engine)
seed(engine)
print("Fictional Karachi Community Pantry data ready.")
