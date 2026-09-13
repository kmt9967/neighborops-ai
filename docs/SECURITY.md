# Security

Secrets belong only in backend environment variables. Never put `OPENROUTER_API_KEY`, a Postgres password, or `SUPABASE_SERVICE_ROLE_KEY` in `NEXT_PUBLIC_*`. The UI calls only FastAPI. The Supabase migration enables RLS without public policies. Inventory and volunteer policy checks run server-side in transactions. The agent has no SQL tool.

This MVP has no operator authentication or organization isolation. It is suitable for a controlled hackathon demo, **not** an internet-exposed production deployment with real requests. Add authentication, authorization, rate limiting, background job execution, and organization-scoped queries before handling real people or public traffic. All seeded people and requests are fictional.
