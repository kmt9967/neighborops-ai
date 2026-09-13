# Architecture

Next.js renders the operator console and calls FastAPI over HTTPS. FastAPI owns all operational state and exposes narrow endpoints for requests, stock, volunteers, the timeline, agent runs, and human decisions. SQLAlchemy targets local SQLite for a zero-account demo or Supabase Postgres via `DATABASE_URL`. The SQL migration enables RLS with no anonymous policies; browser code never receives a database credential.

`POST /api/agent/run` claims each NEW request atomically, creates an `agent_runs` record, and invokes a fresh Strands agent for that request. The Strands OpenAI-compatible provider calls OpenRouter's free router. The model chooses from the registered tools. Every mutating tool validates policy again at the database boundary and writes events. The unique `(request_id, resource_id)` allocation constraint and conditional inventory update prevent double reservation and negative stock.

An unavailable model leaves unprocessed requests NEW and records an error. Actions already committed by a tool remain visible and idempotent. Human decisions are separate API calls and appear in the same timeline.

Deployment: Next.js on Vercel, FastAPI on a Linux Python host, Supabase Postgres. Set CORS `FRONTEND_ORIGINS` to the deployed frontend origin and configure a private `DATABASE_URL` on the backend.
