# Agents for Humans: Building NeighborOps AI with Strands Agents SDK

Community organizations often coordinate assistance with a patchwork of forms, spreadsheets, phone calls, and messages. A food bank may have an incoming request, limited stock, and a volunteer who can deliver it, but connecting those pieces still takes staff time. The same team must also spot missing details and decide when a request would consume resources reserved for others. I built NeighborOps AI for the Agents for Humans Hackathon to explore a practical division of labor: **automate routine coordination, escalate judgment**.

NeighborOps AI is an operational agent, not a chat interface. It reads fictional assistance requests, checks inventory and volunteer availability, reserves appropriate resources, creates delivery tasks, and records what happened. When a policy threshold is at risk, it pauses for a person. The prototype is aimed at nonprofits, food banks, relief groups, schools, libraries, and other local teams whose limited capacity makes careful coordination important.

## Why Strands

I chose the AWS-backed open-source Strands Agents SDK because the central requirement was real tool use. The agent needed to choose among narrow actions, call them, observe their results, and continue based on the updated state. A system prompt gives it the operating rules; application code enforces the rules at each tool boundary. Strands provides the orchestration and model flexibility to keep those responsibilities separate.

For this hackathon I used free-hosted models through OpenRouter, with Strands as the agent framework. The deployed runs used `openrouter/free` and `nex-agi/nex-n2.5-pro:free`. Keeping the model adapter flexible mattered because the project had a $0 out-of-pocket target and free-model availability can vary. The agent behavior is not a scripted simulation: persisted production events show actual Strands tool calls and their effects. The project does not use Amazon Bedrock or Bedrock AgentCore.

## Architecture and tool boundaries

The Next.js frontend presents requests, resources, volunteers, activity, and a human review action. A FastAPI backend invokes the Strands agent. Its model adapter points to OpenRouter. SQLAlchemy persists operational state in Supabase Postgres, and Vercel hosts the frontend and backend. Each agent invocation claims one new request; the UI can invoke it again until the queue is empty.

The agent can call tools such as `get_pending_requests`, `get_request_details`, `classify_request`, `get_inventory`, `check_safety_threshold`, `reserve_inventory`, `get_available_volunteers`, `match_volunteer`, `create_delivery_task`, `schedule_followup`, `request_human_approval`, and `mark_needs_information`. Those names describe specific business operations rather than exposing unrestricted database access. The model cannot issue arbitrary SQL or directly rewrite inventory. The backend validates transitions and writes an audit trail around actions that matter.

That separation is useful in an agentic system. A model may suggest an allocation, but `check_safety_threshold` evaluates the actual protected reserve, and `reserve_inventory` applies database-side constraints. If stock or policy changes between reasoning and action, the transaction must still be safe. The activity timeline makes the resulting decisions inspectable by an operator.

## Human authority where it matters

The key policy is simple: the agent cannot allocate inventory below a configured safety threshold without explicit human approval. One seeded organization request asked for ten food boxes. At that point, fifteen boxes were available, so reserving ten would have left five. The protected floor was eight. The agent checked the numbers and moved the request to `HUMAN_REVIEW` instead of quietly taking the stock.

In the live application, the operator selected `REDUCE_ALLOCATION` and approved four boxes. That left eleven available, above the floor. The system persisted the human decision, the four-box reservation, a volunteer match, a delivery task, and an audit event. The request finished as `SCHEDULED`. This is the distinction I wanted the demo to make: the agent performs coordination, while the person owns the high-impact tradeoff.

Another request lacked a location. The agent did not invent an address or assign a delivery. It marked the request `NEEDS_INFORMATION` and created neither an allocation nor a task. In community work, a plausible-looking guess is not a safe substitute for a missing fact.

## What the production run showed

I validated the hosted flow against five seeded, fictional requests. The final states were two `AUTO_APPROVED`, two `SCHEDULED`, and one `NEEDS_INFORMATION`. The scheduled cases include volunteer coordination and the human-approved reduced allocation. The database contained four unique allocations, four unique tasks, and one human decision. The tool and activity records showed classification, stock checks, reservations, volunteer matching, task creation, human escalation, and missing-information handling.

Inventory changes matched those decisions. Food boxes moved from 15 available / 9 reserved immediately before the human reduction to 11 available / 13 reserved afterward. Baby-care kits moved from 7 available / 3 reserved to 6 available / 4 reserved during the remaining run. Medicine vouchers finished at 4 available / 4 reserved. A final agent invocation processed zero additional requests and changed no inventory or counts. That second run matters: retries should not silently duplicate reservations or deliveries.

The safeguards are in ordinary code as well as in the prompt. Reservations are transaction-safe, completed requests are protected from duplicate processing, inventory cannot go negative, unavailable volunteers cannot be assigned, and missing information remains missing until supplied. Decisions and agent events persist so a human can reconstruct what happened. These controls are especially important when model calls are retried or a free provider is temporarily unavailable.

## Lessons and next steps

I learned that a useful agent needs a small set of well-defined tools more than broad access to a system. Human escalation works best when it follows an explicit threshold, not a vague request to “be careful.” Idempotency is a product feature when software can act autonomously and retry. The activity timeline also matters: users need to see why a request stopped, what was reserved, and who approved an exception. Model flexibility helped this $0 build, but the policy and tool architecture mattered more than any single model.

NeighborOps AI is a hackathon prototype, not a deployed nonprofit service. Multi-organization tenancy, authentication, notifications, background agents, more configurable policies, broader resource categories, and richer observability are future work. Those additions would need the same clear boundaries around authority and data.

You can explore the [live demo](https://neighborops-ai.vercel.app/), inspect the [source and setup instructions](https://github.com/kmt9967/neighborops-ai), and watch the [four-minute demo video](https://youtu.be/rRHNVxvuPsQ). The project was built for the Agents for Humans Hackathon in the Good Neighbor Agents track.

**NeighborOps AI is built around one idea: automate routine coordination, escalate judgment.**
