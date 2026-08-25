alter table public.jobs
    add column if not exists stable_key text,
    add column if not exists source_job_id text not null default '',
    add column if not exists application_deadline timestamptz,
    add column if not exists is_active boolean not null default true,
    add column if not exists missing_runs integer not null default 0;

update public.jobs
set stable_key = normalized_url
where stable_key is null or stable_key = '';

alter table public.jobs alter column stable_key set not null;

create unique index if not exists jobs_user_stable_key_idx
    on public.jobs(user_id, stable_key);

create index if not exists jobs_user_active_score_idx
    on public.jobs(user_id, is_active, score desc);
