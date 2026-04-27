-- Jalankan script ini di Supabase SQL Editor.
-- Tujuan:
-- 1) Menyimpan atribut tester baru (device, browser, no hp)
-- 2) Menjaga submit lintas role tetap konsisten
-- 3) Menampilkan atribut + urutan step lengkap di v_uf_report untuk halaman hasil/CSV/PDF

begin;

alter table if exists public.uf_submissions
  add column if not exists tester_phone text,
  add column if not exists tester_device text,
  add column if not exists tester_browser text;

create or replace function public.uf_submit_full(payload jsonb)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
declare
  p jsonb := coalesce(payload->'payload', payload, '{}'::jsonb);
  t jsonb := coalesce(p->'tester', '{}'::jsonb);

  v_submission_id uuid;
  v_flow_id uuid;
  v_flow_slug text := nullif(trim(coalesce(p->>'flow_slug', p->>'flow')), '');

  v_full_name text := nullif(trim(coalesce(t->>'full_name', t->>'name', p->>'tester_full_name')), '');
  v_org text := nullif(trim(coalesce(t->>'org', t->>'instansi_unit', p->>'tester_org')), '');
  v_email text := nullif(trim(coalesce(t->>'email', p->>'tester_email')), '');
  v_phone text := nullif(trim(coalesce(t->>'phone', t->>'no_hp', p->>'tester_phone')), '');
  v_device text := nullif(trim(coalesce(t->>'device', p->>'tester_device')), '');
  v_browser text := nullif(trim(coalesce(t->>'browser', p->>'tester_browser')), '');

  ans jsonb;
  note_item jsonb;
begin
  if v_flow_slug is null then
    raise exception 'flow_slug wajib diisi';
  end if;

  select f.id into v_flow_id
  from public.uf_flows f
  where f.slug = v_flow_slug
  limit 1;

  if v_flow_id is null then
    raise exception 'Flow tidak ditemukan: %', v_flow_slug;
  end if;

  if v_full_name is null then
    raise exception 'Nama lengkap penguji wajib diisi';
  end if;

  insert into public.uf_submissions (
    flow_id,
    tester_full_name,
    tester_org,
    tester_email,
    tester_phone,
    tester_device,
    tester_browser
  ) values (
    v_flow_id,
    v_full_name,
    v_org,
    v_email,
    v_phone,
    v_device,
    v_browser
  )
  returning id into v_submission_id;

  for ans in
    select value
    from jsonb_array_elements(coalesce(p->'answers', '[]'::jsonb))
  loop
    insert into public.uf_answers (
      submission_id,
      step_id,
      question_id,
      answer_value,
      note_text
    )
    values (
      v_submission_id,
      (ans->>'step_id')::uuid,
      (ans->>'question_id')::uuid,
      nullif(trim(coalesce(ans->>'answer_value', '')), ''),
      nullif(trim(coalesce(ans->>'note_text', '')), '')
    );
  end loop;

  for note_item in
    select value
    from jsonb_array_elements(coalesce(p->'step_notes', '[]'::jsonb))
  loop
    insert into public.uf_step_notes (
      submission_id,
      step_id,
      opinion_text
    )
    values (
      v_submission_id,
      (note_item->>'step_id')::uuid,
      nullif(trim(coalesce(note_item->>'opinion_text', note_item->>'note_text', '')), '')
    );
  end loop;

  return v_submission_id;
end;
$$;

create or replace function public.uf_submit_full(
  answers jsonb,
  flow_slug text,
  step_notes jsonb,
  tester jsonb
)
returns uuid
language plpgsql
security definer
set search_path = public
as $$
begin
  return public.uf_submit_full(
    jsonb_build_object(
      'flow_slug', flow_slug,
      'tester', coalesce(tester, '{}'::jsonb),
      'answers', coalesce(answers, '[]'::jsonb),
      'step_notes', coalesce(step_notes, '[]'::jsonb)
    )
  );
end;
$$;

drop view if exists public.v_uf_report;

create or replace view public.v_uf_report as
select
  s.id as submission_id,
  coalesce(
    nullif(f.role_name, ''),
    case lower(coalesce(f.slug, ''))
      when 'super-admin' then 'Super Admin'
      when 'admin' then 'Admin'
      when 'anggota' then 'Anggota'
      else initcap(replace(coalesce(f.slug, '-'), '-', ' '))
    end
  ) as role_name,
  f.slug as flow_slug,
  s.tester_full_name,
  s.tester_org,
  s.tester_email,
  s.tester_phone,
  s.tester_device,
  s.tester_browser,
  st.step_no as step_order,
  st.step_title,
  st.action_instruction,
  q.question_text,
  a.answer_value,
  a.note_text as question_note,
  to_jsonb(sn)->>'opinion_text' as step_opinion,
  s.submitted_at
from public.uf_submissions s
join public.uf_flows f on f.id = s.flow_id
left join public.uf_answers a on a.submission_id = s.id
left join public.uf_steps st on st.id = a.step_id
left join public.uf_questions q on q.id = a.question_id
left join public.uf_step_notes sn on sn.submission_id = s.id and sn.step_id = a.step_id;

commit;

-- Setelah dijalankan, lakukan submit ulang minimal 1 data untuk tiap role
-- agar atribut tester_device/tester_browser terlihat terisi di halaman hasil.
