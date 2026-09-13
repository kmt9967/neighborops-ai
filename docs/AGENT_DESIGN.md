# Agent design

The agent is a real `strands.Agent` with Strands `@tool` functions. Its system prompt gives policy priorities; the model determines the tool sequence per request. Tools inspect request details, inventory, thresholds, and volunteers, then may classify, reserve, schedule, draft, complete, or escalate. The prompt alone is not the safety boundary: `Operations.reserve` checks inventory and threshold in an atomic update, `create_task` rejects unavailable volunteers, and `complete_routine` requires a real allocation.

`OPENROUTER_MODEL` defaults to `nex-agi/nex-n2-pro:free`, a currently free tool-capable model. `OPENROUTER_FALLBACK_MODEL` defaults to `openrouter/free`, which selects a free model supporting the tools in the request. Paid model IDs are rejected. If both candidates fail, the run records a safe generic error; provider exception text is not logged because it can contain credentials.

No background polling or outbound notification delivery is implied. "Run Agent" explicitly triggers work; notification text is a draft for staff. This keeps the demo free and operationally honest.
