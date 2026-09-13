# Agent design

NeighborOps uses a real `strands.Agent` with 15 registered `@tool` functions. For each claimed request, the model inspects its details and current inventory, then decides which checks and actions to call. A text answer never changes operational state. The API counts a request as processed only after a tool changes its state.

Tools can list requests, inspect details and resources, classify, check protected stock, reserve inventory, find and assign an available volunteer, create a delivery or follow-up task, draft a notification, request human approval, mark missing information, and complete routine processing. The model has no arbitrary SQL or outbound-message tool. `Operations.reserve` checks available stock and safety thresholds with a conditional update; `create_task` rejects unavailable volunteers; `complete_routine` requires an allocation. Human review is required when an allocation would reach the protected reserve.

The primary model is `nex-agi/nex-n2.5-pro:free`; the fallback is `openrouter/free`. Only free model IDs are accepted. A production run may use the fallback when the primary fails or is unavailable, and the recorded `agent_runs.model_used` identifies the model that completed a request. The agent callback is disabled so model content and provider errors are not printed in host logs. If both models fail, the claimed request returns to `NEW`, a generic error is recorded, and prior committed tool actions remain auditable and idempotent. Free-tier daily limits can pause the demo until the provider's reset.

Run Agent is operator-triggered in this MVP. Notifications are drafts, never sent. The Vercel frontend calls the API one request at a time to fit the serverless execution window, then refreshes its dashboard after each completed call.
