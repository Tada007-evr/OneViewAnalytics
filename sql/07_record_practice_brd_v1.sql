-- OneView revised Record Practice Paper BRD v1
-- Apply once in Supabase SQL Editor after the existing schema.
-- Adds optional notes, estimated-grade storage, edit support, and DB-level mark validation.

alter table public.practice_attempts
    add column if not exists notes varchar(300),
    add column if not exists estimated_grade text,
    add column if not exists updated_at timestamptz not null default now();

alter table public.practice_attempts
    drop constraint if exists practice_attempts_notes_length;

alter table public.practice_attempts
    add constraint practice_attempts_notes_length
    check (notes is null or char_length(notes) <= 300);

-- Allow authenticated students to edit their own detailed results.
drop policy if exists "student updates own question results" on public.question_results;
create policy "student updates own question results"
on public.question_results
for update
using (
    exists (
        select 1
        from public.practice_attempts a
        where a.attempt_id = question_results.attempt_id
          and a.student_id = auth.uid()
    )
)
with check (
    exists (
        select 1
        from public.practice_attempts a
        where a.attempt_id = question_results.attempt_id
          and a.student_id = auth.uid()
    )
);

drop policy if exists "student updates own subpart results" on public.subpart_results;
create policy "student updates own subpart results"
on public.subpart_results
for update
using (
    exists (
        select 1
        from public.question_results qr
        join public.practice_attempts a on a.attempt_id = qr.attempt_id
        where qr.question_result_id = subpart_results.question_result_id
          and a.student_id = auth.uid()
    )
)
with check (
    exists (
        select 1
        from public.question_results qr
        join public.practice_attempts a on a.attempt_id = qr.attempt_id
        where qr.question_result_id = subpart_results.question_result_id
          and a.student_id = auth.uid()
    )
);

-- Enforce score <= maximum marks at the database boundary.
create or replace function public.validate_question_result_score()
returns trigger
language plpgsql
as $$
declare
    allowed numeric(8,2);
begin
    select q.max_marks into allowed
    from public.questions q
    where q.question_id = new.question_id;

    if new.score < 0 or new.score > allowed then
        raise exception 'Question score % must be between 0 and maximum marks %', new.score, allowed;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_validate_question_result_score on public.question_results;
create trigger trg_validate_question_result_score
before insert or update of score, question_id
on public.question_results
for each row execute function public.validate_question_result_score();

create or replace function public.validate_subpart_result_score()
returns trigger
language plpgsql
as $$
declare
    allowed numeric(8,2);
begin
    select sp.max_marks into allowed
    from public.sub_parts sp
    where sp.sub_part_id = new.sub_part_id;

    if new.score < 0 or new.score > allowed then
        raise exception 'Sub-part score % must be between 0 and maximum marks %', new.score, allowed;
    end if;
    return new;
end;
$$;

drop trigger if exists trg_validate_subpart_result_score on public.subpart_results;
create trigger trg_validate_subpart_result_score
before insert or update of score, sub_part_id
on public.subpart_results
for each row execute function public.validate_subpart_result_score();

create or replace function public.set_practice_attempt_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_practice_attempt_updated_at on public.practice_attempts;
create trigger trg_practice_attempt_updated_at
before update on public.practice_attempts
for each row execute function public.set_practice_attempt_updated_at();

-- Extend the existing history view so Reports / View / Edit can consume BRD fields.
create or replace view public.v_attempt_history
with (security_invoker=true) as
select
    a.attempt_id,
    a.student_id,
    a.attempt_date,
    p.year,
    p.session,
    p.paper_code,
    a.total_score,
    p.total_marks,
    a.percentage,
    a.estimated_grade,
    a.notes,
    a.updated_at
from public.practice_attempts a
join public.exam_papers p on p.paper_id = a.paper_id
where a.status = 'completed';
