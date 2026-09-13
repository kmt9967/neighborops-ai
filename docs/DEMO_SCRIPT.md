# 3–4 minute judge demo

Record the [live app](https://neighborops-ai.vercel.app/) at desktop width. The five seeded people and their requests are fictional. The official limit is five minutes; aim for about 3:45. If live free-model inference takes longer, cut or speed up only waiting time and label that edit. Do not substitute fabricated results.

1. **0:00–0:30 — Problem and audience.** Open `/`. “Small community pantries spend their day triaging requests and matching stock and volunteers. NeighborOps takes routine coordination off the team’s plate while leaving consequential decisions with people.” Show the dashboard counts.
2. **0:30–1:00 — Current capacity.** Open `/requests`, `/resources`, and `/volunteers`. Show five intake cases, the eight-box protected food reserve, and two available volunteers. “The agent sees operational constraints, not just a chat prompt.”
3. **1:00–2:05 — Real agent work.** Return to `/` and click **Run Agent**. Show the working state and at least one count update. Explain that Strands chooses registered tools to inspect, classify, reserve, match, schedule, or escalate. Open `/activity` after completion and point to persisted tool events. Show the model recorded for the run if presenting API evidence.
4. **2:05–2:35 — Routine and missing information.** Open an auto-handled request and show its allocation and volunteer task. Open `REQ-005`; show **Needs Information** and no invented address or allocation.
5. **2:35–3:20 — Human judgment.** Open `REQ-004`, the ten-box event request. Show **Human Review** because the protected food stock would be breached. Select **Reduce allocation**, enter `4`, and save. Show the human decision event, the four-box reservation, and the downstream task.
6. **3:20–3:45 — Safe retry.** Return to `/`, click **Run Agent** again, and show zero duplicate processing. “The agent can retry safely; allocations have a unique constraint and inventory is reserved transactionally. Automate routine coordination. Escalate judgment.”

If the free model is unavailable, show the explicit error and unchanged operational data. Do not claim the agent completed requests.
