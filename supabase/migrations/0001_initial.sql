create extension if not exists pgcrypto;

create table public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text not null default '',
    created_at timestamptz not null default now()
);

create table public.search_profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    name text not null default 'PFE AI France',
    config jsonb not null default '{}'::jsonb,
    active boolean not null default true,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.jobs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    title text not null,
    company text not null default '',
    location text not null default '',
    description text not null default '',
    canonical_url text not null,
    normalized_url text not null,
    score integer not null default 0,
    score_explanation jsonb not null default '{}'::jsonb,
    status text not null default 'new' check (
        status in ('new', 'shortlisted', 'preparing', 'ready', 'applied', 'interview', 'rejected', 'offer', 'ignored')
    ),
    published_at timestamptz,
    first_seen_at timestamptz not null default now(),
    last_seen_at timestamptz not null default now(),
    unique (user_id, normalized_url)
);

create index jobs_user_score_idx on public.jobs(user_id, score desc);
create index jobs_user_status_idx on public.jobs(user_id, status);

create table public.job_sources (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    job_id uuid not null references public.jobs(id) on delete cascade,
    source text not null,
    source_job_id text,
    source_url text not null,
    discovered_at timestamptz not null default now(),
    unique (user_id, source, source_url)
);

create table public.collector_runs (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    source text not null,
    status text not null check (status in ('running', 'succeeded', 'failed', 'blocked')),
    jobs_seen integer not null default 0,
    jobs_saved integer not null default 0,
    error text,
    started_at timestamptz not null default now(),
    finished_at timestamptz
);

create table public.applications (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    job_id uuid not null references public.jobs(id) on delete cascade,
    status text not null default 'shortlisted',
    notes text not null default '',
    applied_at timestamptz,
    follow_up_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (user_id, job_id)
);

create table public.documents (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    application_id uuid references public.applications(id) on delete cascade,
    kind text not null check (kind in ('cv', 'cover_letter', 'answers')),
    storage_path text not null,
    created_at timestamptz not null default now()
);

alter table public.profiles enable row level security;
alter table public.search_profiles enable row level security;
alter table public.jobs enable row level security;
alter table public.job_sources enable row level security;
alter table public.collector_runs enable row level security;
alter table public.applications enable row level security;
alter table public.documents enable row level security;

create policy "users manage own profile" on public.profiles
    for all to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);
create policy "users manage own search profiles" on public.search_profiles
    for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own jobs" on public.jobs
    for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own job sources" on public.job_sources
    for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users view own collector runs" on public.collector_runs
    for select to authenticated using ((select auth.uid()) = user_id);
create policy "users manage own applications" on public.applications
    for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "users manage own documents" on public.documents
    for all to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
