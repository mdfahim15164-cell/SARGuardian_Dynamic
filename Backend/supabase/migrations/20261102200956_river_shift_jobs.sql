-- Durable, owner-scoped RiverShift GCOV jobs and private result receipts.
-- Raw NISAR products and derived layers remain in private object storage, not in Postgres.
begin;

-- This project-level SECURITY DEFINER helper is used by an enabled event trigger
-- to turn RLS on for new public tables. It must not be callable by Data API users.
revoke execute on function public.rls_auto_enable() from public, anon, authenticated;

create table public.river_shift_jobs (
  id uuid primary key default gen_random_uuid(),
  owner_uid text not null check (length(btrim(owner_uid)) > 0),
  idempotency_key text not null check (idempotency_key ~ '^[A-Za-z0-9._:-]{16,128}$'),
  state public.processing_job_state not null default 'queued',
  stage text not null default 'queued' check (length(stage) between 1 and 100),
  aoi_wkt text not null check (length(aoi_wkt) between 20 and 100000),
  start_date date not null,
  end_date date not null check (end_date >= start_date),
  maturity text not null check (maturity in ('PROVISIONAL', 'BETA')),
  frequency text not null check (frequency in ('frequencyA', 'frequencyB')),
  covariance_term text not null check (covariance_term in ('HHHH', 'HVHV', 'VVVV', 'VHVH', 'RHRH', 'RVRV')),
  request_fingerprint text not null check (request_fingerprint ~ '^[a-f0-9]{64}$'),
  request_snapshot jsonb not null check (jsonb_typeof(request_snapshot) = 'object'),
  manifest_snapshot jsonb not null check (jsonb_typeof(manifest_snapshot) = 'object'),
  github_run_id text,
  github_run_url text,
  callback_sequence integer not null default 0 check (callback_sequence between 0 and 1000),
  error_code text,
  error_message text,
  result_summary jsonb,
  artifact_manifest jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (owner_uid, idempotency_key)
);

create index river_shift_jobs_owner_created_idx
  on public.river_shift_jobs (owner_uid, created_at desc);
create index river_shift_jobs_state_idx on public.river_shift_jobs (state);
create unique index river_shift_jobs_one_active_per_owner_idx
  on public.river_shift_jobs (owner_uid)
  where state in ('queued', 'dispatching', 'running');

create or replace function public.enforce_river_shift_job_transition()
returns trigger language plpgsql set search_path = public as $$
begin
  if tg_op = 'INSERT' then
    if new.state <> 'queued' then raise exception 'new RiverShift jobs must start queued'; end if;
    return new;
  end if;
  if new.state <> old.state and not (
    (old.state = 'queued' and new.state in ('dispatching', 'failed', 'cancelled')) or
    (old.state = 'dispatching' and new.state in ('running', 'failed', 'cancelled')) or
    (old.state = 'running' and new.state in ('succeeded', 'failed', 'cancelled'))
  ) then raise exception 'invalid RiverShift job transition: % -> %', old.state, new.state; end if;
  if new.owner_uid is distinct from old.owner_uid
    or new.idempotency_key is distinct from old.idempotency_key
    or new.aoi_wkt is distinct from old.aoi_wkt
    or new.start_date is distinct from old.start_date
    or new.end_date is distinct from old.end_date
    or new.maturity is distinct from old.maturity
    or new.frequency is distinct from old.frequency
    or new.covariance_term is distinct from old.covariance_term
    or new.request_fingerprint is distinct from old.request_fingerprint
    or new.request_snapshot is distinct from old.request_snapshot
    or new.manifest_snapshot is distinct from old.manifest_snapshot
  then raise exception 'RiverShift request inputs are immutable'; end if;
  if new.callback_sequence < old.callback_sequence
    or new.callback_sequence > old.callback_sequence + 1 then
    raise exception 'RiverShift callback sequence is invalid';
  end if;
  new.updated_at = now();
  return new;
end;
$$;

create trigger river_shift_jobs_transition_guard
before insert or update on public.river_shift_jobs
for each row execute function public.enforce_river_shift_job_transition();

alter table public.river_shift_jobs enable row level security;
revoke all on table public.river_shift_jobs from public, anon, authenticated;
grant select, insert, update on table public.river_shift_jobs to service_role;
create policy river_shift_jobs_owner_read on public.river_shift_jobs
  for select to authenticated
  using ((select auth.jwt() ->> 'sub') = owner_uid);

comment on table public.river_shift_jobs is
  'Authenticated RiverShift NISAR GCOV jobs, immutable discovery manifest, signed worker state and private derived-result receipt; no raw radar files.';
comment on column public.river_shift_jobs.manifest_snapshot is
  'Exact server-refreshed CMR GCOV metadata selected for this request; no download claim.';
comment on column public.river_shift_jobs.artifact_manifest is
  'Private Google Drive artifact inventory with exact paths, checksums and byte sizes; never a public URL.';

commit;
