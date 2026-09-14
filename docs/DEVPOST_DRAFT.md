# Devpost draft — Agents for Humans / Good Neighbor Agents

This is copy-ready text for the [NeighborOps AI Devpost draft](https://devpost.com/submit-to/30317-agents-for-humans-hackathon/manage/submissions/1180456-neighborops-ai/project-overview). The separate pre-existing **Untitled** draft was left untouched. NeighborOps AI has a saved draft, but no final submission has been made. The official deadline is September 14, 2026 at 5:00 p.m. PDT (September 15 at 5:00 a.m. Pakistan time).

## Project overview

**Project name:** NeighborOps AI

**Elevator pitch:** A Strands agent coordinates routine community requests while people decide how to use scarce resources.

## About the project

### Inspiration

Small community organizations receive requests through scattered channels but have limited staff time to classify each need, compare it with stock, find an available volunteer, and follow up. Those steps are repetitive, yet some choices—especially those that consume protected inventory—require human judgment. We built NeighborOps AI to handle the routine coordination and make escalation visible.

### What it does

NeighborOps is an operations dashboard for a fictional Karachi Community Pantry. Five seeded requests exercise three paths: safe routine coordination, missing information, and a high-impact allocation requiring human review. An operator clicks **Run Agent**; a real Strands agent inspects the request and current capacity through tools, then classifies, reserves, assigns, schedules, drafts a notification, or escalates. Inventory and volunteers update only when policy-enforcing tools succeed. A missing address is not invented. The activity page records the actual operations.

For the large community-event request, reserving ten food boxes would cross a protected stock threshold. The agent asks for human review. The operator can reduce the allocation to four, after which reservation and volunteer coordination continue. A second agent run does not duplicate completed allocations.

The hosted Strands/OpenRouter runs processed all five fictional requests with real tool calls. Two are `AUTO_APPROVED`, two are `SCHEDULED`, and one is `NEEDS_INFORMATION` for a missing location. The ten-box event request reached genuine `HUMAN_REVIEW` because it would have breached the eight-box protected reserve. An operator chose `REDUCE_ALLOCATION` to four through the live UI; the decision, reservation, volunteer match, and task persisted. Food stock finished at 11 available / 13 reserved. Four allocations, four tasks, and one human decision remain unique. A final agent run processed zero requests with inventory and counts unchanged.

### How we built it

The frontend is Next.js on Vercel Hobby. FastAPI, also on Vercel Hobby, invokes `strands.Agent` with 15 narrow `@tool` functions. Strands uses an OpenAI-compatible model adapter pointed at OpenRouter's free-model endpoint. The fallback free router handles temporary primary-model unavailability. SQLAlchemy stores requests, resources, allocations, volunteers, tasks, decisions, runs, and audit events in a dedicated Supabase Postgres project over verified TLS. Each serverless invocation claims one new request atomically; the frontend repeats the call until the queue is empty. The repository includes a SQL migration, idempotent seed, policy tests, and an architecture diagram.

### Human control and safety

The model has no general database or messaging tool. Reservations use transactional stock checks and a unique allocation constraint; volunteer assignments require an available, suitable volunteer; routine completion requires a real allocation. Threshold breaches create a human-review record rather than silently allocating. Notifications are drafts and are never sent automatically. Provider errors produce a generic retry state without exposing credentials or claiming success.

### Challenges and learning

Free models vary in availability and tool-call reliability. We learned to treat the model as a planner, not as the source of truth: every operational mutation must be validated at the tool and database boundary. The hosted demo also required bounded per-request runs for serverless execution and an explicit trusted certificate for the Supabase pooler. A failed model attempt can be retried without double-reserving stock.

### What's next

The MVP uses fictional data. Before real organizations use it, we would add operator authentication, organization isolation, intake integrations, rate limits, background jobs, policy configuration, and real notification delivery. We would then measure time saved and response quality with partner organizations rather than assuming impact from a demo.

## Form values and assets

- **Track:** Good Neighbor Agents.
- **Built with:** Strands Agents SDK, Python, FastAPI, Next.js, TypeScript, SQLAlchemy, Supabase Postgres, OpenRouter, Vercel.
- **Public code repo:** https://github.com/kmt9967/neighborops-ai
- **Live demo:** https://neighborops-ai.vercel.app/
- **Architecture diagram file:** [`architecture.png`](architecture.png), generated from [`architecture.dot`](architecture.dot); Mermaid source is in [`ARCHITECTURE.md`](ARCHITECTURE.md).
- **Testing instructions:** Inspect the five final request states from the dashboard. `REQ-004` shows the recorded human four-box reduction, reservation, volunteer match, and task; `REQ-005` shows missing location with no allocation or task. Agent Activity contains persisted Strands tool calls. Food stock is 11 available / 13 reserved. Running the agent once more processes zero requests without changing inventory. Do not reset hosted data or enter real beneficiary information.
- **Video demo link:** [3:58 YouTube demo](https://youtu.be/rRHNVxvuPsQ), uploaded as Unlisted and confirmed playable; the Devpost draft embeds it.
- **AWS Builder ID:** required, must be supplied by the account owner in **Additional info → AWS Builder ID**, immediately below the architecture-diagram upload.
- **Submitter type:** required, must be chosen by the account owner in **Additional info → Submitter Type**, the first dropdown.
- **Country of residence:** required, must be chosen by the account owner in **Additional info → Please indicate your Country of Residence**, the multi-select immediately after Submitter Type.
- **Image gallery:** eight genuine live-production screenshots are uploaded and saved in this order: dashboard, requests, agent activity, auto-handled request, resources, volunteers, human review, needs information. The source captures and captions are documented in [`submission-screenshots/README.md`](submission-screenshots/README.md).

The saved draft has its title, tagline, verified production story, track, repository link, live demo link, testing instructions, architecture PNG, eight-image gallery, and playable YouTube embed. Its Built With tags list Strands, agents, FastAPI, SQLAlchemy, OpenRouter, Next.js, Supabase, Vercel, Python, and TypeScript. Submitter type, country of residence, and AWS Builder ID remain blank for the owner. The form has an optional organization name, optional bonus blog URL, and a final submission step. Do not click the final Submit action without the owner's explicit instruction.
