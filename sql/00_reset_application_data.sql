-- OneView application-data reset
-- WARNING: destructive. This removes all OneView application data in public tables.
-- It intentionally preserves Supabase Auth users in auth.users.
-- After running this file, reload metadata with 04_load_workbook_metadata.sql,
-- recreate public.students rows for the auth users you want to keep,
-- optionally reload historical scores, then apply BI/revised-BRD migrations.

begin;

truncate table
    public.subpart_results,
    public.question_results,
    public.practice_attempts,
    public.subpart_topics,
    public.question_topics,
    public.sub_parts,
    public.questions,
    public.exam_papers,
    public.subtopics,
    public.topics,
    public.students
restart identity cascade;

commit;

-- Validation: all application tables below should now return 0.
select
    (select count(*) from public.students) as students,
    (select count(*) from public.topics) as topics,
    (select count(*) from public.subtopics) as subtopics,
    (select count(*) from public.exam_papers) as papers,
    (select count(*) from public.questions) as questions,
    (select count(*) from public.sub_parts) as subparts,
    (select count(*) from public.practice_attempts) as attempts,
    (select count(*) from public.question_results) as question_results,
    (select count(*) from public.subpart_results) as subpart_results;
