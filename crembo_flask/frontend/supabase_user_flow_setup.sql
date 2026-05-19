-- Setup Supabase untuk fitur User Flow Black Box & SUS Crembo Media.
-- Jalankan file ini di Supabase SQL Editor project: lzdcuvyxksyoozvhcfyj.
-- Catatan keamanan: policy di bawah dibuat terbuka agar halaman HTML statis dapat insert/select/delete memakai publishable key.
-- Untuk produksi final, sebaiknya batasi delete/select dengan autentikasi admin.

create extension if not exists pgcrypto;

create table if not exists public.user_flow_submissions (
  id uuid primary key default gen_random_uuid(),
  flow_slug text not null,
  role_name text not null,
  tester_full_name text not null,
  tester_role text,
  tester_org text,
  test_date text,
  tester_device text,
  tester_browser text,
  blackbox_total integer default 0,
  blackbox_valid integer default 0,
  blackbox_invalid integer default 0,
  blackbox_pending integer default 0,
  sus_score numeric(6,2),
  sus_category text,
  sus_grade text,
  payload jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_user_flow_submissions_created_at on public.user_flow_submissions (created_at desc);
create index if not exists idx_user_flow_submissions_role on public.user_flow_submissions (role_name);
create index if not exists idx_user_flow_submissions_flow on public.user_flow_submissions (flow_slug);

alter table public.user_flow_submissions enable row level security;

drop policy if exists "uf_public_insert" on public.user_flow_submissions;
drop policy if exists "uf_public_select" on public.user_flow_submissions;
drop policy if exists "uf_public_delete" on public.user_flow_submissions;

create policy "uf_public_insert" on public.user_flow_submissions
for insert to anon, authenticated
with check (true);

create policy "uf_public_select" on public.user_flow_submissions
for select to anon, authenticated
using (true);

create policy "uf_public_delete" on public.user_flow_submissions
for delete to anon, authenticated
using (true);
