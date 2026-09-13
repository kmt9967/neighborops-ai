-- Run in Supabase SQL editor. Backend uses a direct Postgres DATABASE_URL, never browser access.
create table if not exists organizations (id text primary key, name text not null);
create table if not exists requests (
 id text primary key, organization_id text not null references organizations(id), requester_name text not null,
 requester_contact text, category text not null, description text not null, household_size integer, location text,
 urgency text not null, status text not null, structured_data jsonb not null default '{}', reasoning_summary text,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now());
create table if not exists resources (
 id text primary key, organization_id text not null references organizations(id), name text not null, type text not null,
 total_quantity integer not null check(total_quantity>=0), available_quantity integer not null check(available_quantity>=0),
 reserved_quantity integer not null check(reserved_quantity>=0), safety_threshold integer not null check(safety_threshold>=0),
 updated_at timestamptz not null default now());
create table if not exists volunteers (
 id text primary key, organization_id text not null references organizations(id), name text not null,
 transport_type text not null, availability boolean not null, max_capacity text not null, skills jsonb not null default '[]',
 current_load integer not null default 0 check(current_load>=0), created_at timestamptz not null default now());
create table if not exists allocations (
 id text primary key, request_id text not null references requests(id), resource_id text not null references resources(id),
 quantity integer not null check(quantity>0), volunteer_id text references volunteers(id), status text not null,
 created_at timestamptz not null default now(), unique(request_id,resource_id));
create table if not exists agent_runs (
 id text primary key, organization_id text not null references organizations(id), status text not null,
 started_at timestamptz not null default now(), completed_at timestamptz, model_used text,
 requests_processed integer not null default 0, error_message text);
create table if not exists agent_events (
 id text primary key, agent_run_id text references agent_runs(id), request_id text references requests(id),
 event_type text not null, message text not null, metadata jsonb not null default '{}', created_at timestamptz not null default now());
create table if not exists human_decisions (
 id text primary key, request_id text not null references requests(id), reason text not null, recommended_option text,
 available_options jsonb not null, selected_option text, decision_notes text, decided_at timestamptz,
 created_at timestamptz not null default now());
create table if not exists tasks (
 id text primary key, request_id text not null unique references requests(id), volunteer_id text references volunteers(id),
 type text not null, status text not null, due_at timestamptz, created_at timestamptz not null default now());
create table if not exists notifications (
 id text primary key, request_id text not null references requests(id), event_type text not null,
 draft text not null, created_at timestamptz not null default now());
create index if not exists requests_status_idx on requests(status);
create index if not exists events_created_idx on agent_events(created_at desc);
create index if not exists events_request_idx on agent_events(request_id);
alter table organizations enable row level security;
alter table requests enable row level security;
alter table resources enable row level security;
alter table volunteers enable row level security;
alter table allocations enable row level security;
alter table agent_runs enable row level security;
alter table agent_events enable row level security;
alter table human_decisions enable row level security;
alter table tasks enable row level security;
alter table notifications enable row level security;
-- No anon policies: all operational access is through the backend's direct database connection.
