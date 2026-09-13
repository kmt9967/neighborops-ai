# 3–4 minute judge demo

Record the [live app](https://neighborops-ai.vercel.app/) at desktop width after the remaining production requests and human decision have been verified. The five seeded people and their requests are fictional. The official limit is five minutes; aim for about 3:55. If live free-model inference takes longer, cut or speed up only waiting time and label that edit. Do not substitute fabricated results. Keep the existing two real allocations and audit events intact while preparing the recording.

1. **0:00–0:20 — Problem.** Open `/`. “Small community groups coordinate limited supplies, volunteers, and incoming requests by hand. NeighborOps takes routine coordination off the team’s plate while leaving consequential decisions with people.”
2. **0:20–1:00 — Capacity and intake.** Show the dashboard, `/resources`, `/volunteers`, then `/requests`. Point out the eight-box protected food reserve and the five fictional requests. “The agent sees operational constraints, not just a chat prompt.”
3. **1:00–2:00 — Real agent work.** Click **Run Agent** for the remaining requests while recording. Show the working state, then `/activity` with persisted classification, inventory, matching, and escalation events. Explain that Strands chooses registered tools; the model's text alone cannot change stock. Label any cut waiting time.
4. **2:00–2:40 — Routine and missing information.** Open a completed request to show its allocation and volunteer task. Open `REQ-005`; show **Needs Information** and no invented address or allocation.
5. **2:40–3:15 — Human judgment.** Open `REQ-004`, the ten-box event request. Show **Human Review** because the protected food stock would be breached. Select **Reduce allocation**, enter `4`, and save. Show the human decision event, four-box reservation, and downstream task.
6. **3:15–3:35 — Safe retry.** Show updated inventory and activity. Click **Run Agent** again and show zero duplicate processing. “Allocations have a unique constraint and inventory is reserved transactionally.”
7. **3:35–3:55 — Architecture.** Briefly show the diagram: Next.js → FastAPI → Strands Agents SDK → OpenRouter free model and narrow tools → Supabase Postgres, with a human decision at the protected-stock boundary. “NeighborOps automates routine coordination and escalates judgment.”

If the free model is unavailable, show the explicit error and unchanged operational data. Do not claim the agent completed requests.
