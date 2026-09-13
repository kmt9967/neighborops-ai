# Security

`OPENROUTER_API_KEY` and `DATABASE_URL` are backend-only environment variables. The repository-root `.env` is ignored by Git and loaded only for local backend execution. Vercel stores production values as secret variables. The Next.js project has only `NEXT_PUBLIC_API_URL`. The current implementation uses direct Postgres access, so neither a Supabase anon key nor service-role key is needed. No secret belongs in a `NEXT_PUBLIC_*` variable or a Devpost asset.

The Supabase migration enables RLS on operational tables without anonymous policies. The API connects through the session pooler using `sslmode=verify-full` and the bundled public CA certificate. Browser requests are restricted to localhost and the exact production Vercel origin by CORS. The agent receives only narrow tool functions, and inventory/volunteer constraints are checked inside server-side transactions. Model output and provider exceptions are suppressed in host logs.

This is an unauthenticated public demo using fictional people and requests. CORS does not authenticate callers. Before real use, add operator authentication and authorization, organization-scoped queries, request-rate limits, audit retention, a background job queue, and secret rotation procedures. Do not enter real beneficiary information in the demo.
