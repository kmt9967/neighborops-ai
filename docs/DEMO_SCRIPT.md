# 3–4 minute judge demo

The [3:58 uploaded demo](https://youtu.be/rRHNVxvuPsQ) and [live app](https://neighborops-ai.vercel.app/) show a fictional organization. This outline records the intended judge narrative. The five-request production flow, human reduction, and final zero-work run were subsequently verified; the live database is now in its final state. The [gallery screenshots](submission-screenshots/README.md) preserve the genuine human-review and missing-information states. Do not reset production data to replay them.

1. **0:00–0:20 — Problem.** Open `/`. “Small community groups coordinate limited supplies, volunteers, and incoming requests by hand. NeighborOps takes routine coordination off the team’s plate while leaving consequential decisions with people.”
2. **0:20–1:00 — Capacity and intake.** Show the dashboard, `/resources`, `/volunteers`, then `/requests`. Point out the eight-box protected food reserve and the five fictional requests. “The agent sees operational constraints, not just a chat prompt.”
3. **1:00–2:00 — Real agent work.** Show `/activity` with persisted classification, inventory, matching, and escalation events. Explain that Strands chooses registered tools; the model's text alone cannot change stock. Label any cut waiting time.
4. **2:00–2:40 — Routine and missing information.** Open a completed request to show its allocation and volunteer task. Open `REQ-005`; show **Needs Information** and no invented address or allocation.
5. **2:40–3:15 — Human judgment.** Use the saved pre-decision screenshot to show `REQ-004` in **Human Review** because the protected food stock would be breached. The live request now shows the operator's **Reduce allocation** decision, four-box reservation, and downstream task.
6. **3:15–3:35 — Safe retry.** Show updated inventory and activity. The verified final run processed zero requests, with no duplicate allocations or tasks. “Allocations have a unique constraint and inventory is reserved transactionally.”
7. **3:35–3:55 — Architecture.** Briefly show the diagram: Next.js → FastAPI → Strands Agents SDK → OpenRouter free model and narrow tools → Supabase Postgres, with a human decision at the protected-stock boundary. “NeighborOps automates routine coordination and escalates judgment.”

If the free model is unavailable, show the explicit error and unchanged operational data. Do not claim the agent completed requests.
