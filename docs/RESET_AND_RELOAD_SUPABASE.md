# OneView — clean reset and reload of Supabase

This procedure rebuilds the OneView **application data** from the beginning while preserving Supabase Authentication accounts in `auth.users`.

> Why preserve Auth? `public.students.student_id` references `auth.users.id`. Deleting Auth users would invalidate family/student logins and requires recreating passwords or invitations. If you truly want Auth users deleted too, do that separately in Supabase Authentication after confirming you want to remove all logins.

## 0. Backup first
Export or snapshot the current Supabase database before running the destructive reset.

## 1. Reset all OneView public application data
Run `sql/00_reset_application_data.sql` in Supabase SQL Editor.

Expected validation result: all listed public application tables return 0 rows.

## 2. Recreate the base schema if starting from an empty project
If the tables themselves do not exist, run `sql/01_schema.sql` first. If they already exist, do not rerun it unless you intentionally want to refresh policies/schema definitions.

## 3. Load the verified workbook metadata
Run `sql/04_load_workbook_metadata.sql`.

This repopulates the Question Mapping Database from the verified workbook data currently in the repository: topics, subtopics, exam papers, questions, sub-parts and mappings.

Do **not** use `sql/02_real_dataset_seed.sql` for this rebuild. It is retained only as an older generated artifact and has previously caused hard-coded UUID foreign-key conflicts.

## 4. Recreate student profile rows for existing Supabase Auth users
For each Auth user who should use OneView, insert the matching row into `public.students` using the exact `auth.users.id` UUID.

Example:

```sql
insert into public.students (student_id, name, academic_level, subject)
values ('AUTH-USER-UUID-HERE', 'Student Name', 'AS Level', 'Mathematics')
on conflict (student_id) do update
set name = excluded.name,
    academic_level = excluded.academic_level,
    subject = excluded.subject;
```

Check Auth UUIDs with:

```sql
select id, email from auth.users order by email;
```

## 5. Apply revised BRD migration
Run `sql/07_record_practice_brd_v1.sql`.

This enables notes, estimated-grade storage, edit permissions, timestamps and database-level max-mark validation.

## 6. Recreate BI views
Run `sql/03_bi_views.sql` after the BRD migration. If `07_record_practice_brd_v1.sql` extends `v_attempt_history`, run `07` last so its extended history definition remains active.

Recommended order for the current repository is therefore:

1. `00_reset_application_data.sql`
2. `04_load_workbook_metadata.sql`
3. recreate `public.students`
4. `03_bi_views.sql`
5. `07_record_practice_brd_v1.sql`

## 7. Historical scores are optional
If you want the previously supplied workbook's historical practice scores restored, update the student UUID placeholder in `sql/06_optional_load_existing_scores.sql` and run it only after the matching `public.students` row exists.

If you want a truly fresh student history, **do not run 06**. Students will start with zero attempts and enter new practice through the UI.

## 8. Validation queries

```sql
select count(*) as students from public.students;
select count(*) as topics from public.topics;
select count(*) as subtopics from public.subtopics;
select count(*) as papers from public.exam_papers;
select count(*) as questions from public.questions;
select count(*) as subparts from public.sub_parts;
select count(*) as attempts from public.practice_attempts;
```

Also verify paper totals:

```sql
select year, session, paper_code, total_marks
from public.exam_papers
order by year, session, paper_code;
```

## 9. End-to-end test
1. Sign in to deployed Streamlit.
2. Verify Overview loads.
3. Open Record Practice Paper.
4. Verify Paper/Session/Year and question mappings load from Supabase.
5. Enter a valid score and confirm totals/percentage/topic summary.
6. Attempt an invalid score above maximum and confirm rejection.
7. Save.
8. Verify the record appears in Practice Records, Overview, Topic Analysis, Progress and Reports.
9. Edit the saved record and verify analytics update.
10. Test a second student account and confirm RLS isolation.

## Paper 5 note
The revised BRD requires Paper 1 and Paper 5, but the repository currently has verified Paper 1 mapping data only. The reset/reload process will therefore restore only the verified data currently available. Do not fabricate Paper 5 mappings; load them after the verified Paper 5 workbook is supplied.
