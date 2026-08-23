-- OneView October 2026 release hardening
-- Applied to production Supabase after the August 2026 clean reload.

-- Pin function search paths.
alter function public.validate_question_result_score() set search_path = public, pg_temp;
alter function public.validate_subpart_result_score() set search_path = public, pg_temp;
alter function public.set_practice_attempt_updated_at() set search_path = public, pg_temp;

-- Internal helper must not be exposed through PostgREST RPC.
revoke execute on function public.rls_auto_enable() from public, anon, authenticated;

-- Cover foreign-key and analytics access paths.
create index if not exists idx_practice_attempts_paper_id on public.practice_attempts(paper_id);
create index if not exists idx_question_results_question_id on public.question_results(question_id);
create index if not exists idx_question_topics_topic_id on public.question_topics(topic_id);
create index if not exists idx_question_topics_subtopic_id on public.question_topics(subtopic_id);
create index if not exists idx_subpart_results_sub_part_id on public.subpart_results(sub_part_id);
create index if not exists idx_subpart_topics_topic_id on public.subpart_topics(topic_id);
create index if not exists idx_subpart_topics_subtopic_id on public.subpart_topics(subtopic_id);

-- Avoid per-row auth.uid() re-evaluation at scale.
drop policy if exists "student reads own profile" on public.students;
create policy "student reads own profile" on public.students for select using (student_id = (select auth.uid()));
drop policy if exists "student inserts own profile" on public.students;
create policy "student inserts own profile" on public.students for insert with check (student_id = (select auth.uid()));
drop policy if exists "student updates own profile" on public.students;
create policy "student updates own profile" on public.students for update using (student_id = (select auth.uid())) with check (student_id = (select auth.uid()));

drop policy if exists "student reads own attempts" on public.practice_attempts;
create policy "student reads own attempts" on public.practice_attempts for select using (student_id = (select auth.uid()));
drop policy if exists "student inserts own attempts" on public.practice_attempts;
create policy "student inserts own attempts" on public.practice_attempts for insert with check (student_id = (select auth.uid()));
drop policy if exists "student updates own attempts" on public.practice_attempts;
create policy "student updates own attempts" on public.practice_attempts for update using (student_id = (select auth.uid())) with check (student_id = (select auth.uid()));

drop policy if exists "student reads own question results" on public.question_results;
create policy "student reads own question results" on public.question_results for select using (exists (select 1 from public.practice_attempts a where a.attempt_id=question_results.attempt_id and a.student_id=(select auth.uid())));
drop policy if exists "student inserts own question results" on public.question_results;
create policy "student inserts own question results" on public.question_results for insert with check (exists (select 1 from public.practice_attempts a where a.attempt_id=question_results.attempt_id and a.student_id=(select auth.uid())));
drop policy if exists "student updates own question results" on public.question_results;
create policy "student updates own question results" on public.question_results for update using (exists (select 1 from public.practice_attempts a where a.attempt_id=question_results.attempt_id and a.student_id=(select auth.uid()))) with check (exists (select 1 from public.practice_attempts a where a.attempt_id=question_results.attempt_id and a.student_id=(select auth.uid())));

drop policy if exists "student reads own subpart results" on public.subpart_results;
create policy "student reads own subpart results" on public.subpart_results for select using (exists (select 1 from public.question_results qr join public.practice_attempts a on a.attempt_id=qr.attempt_id where qr.question_result_id=subpart_results.question_result_id and a.student_id=(select auth.uid())));
drop policy if exists "student inserts own subpart results" on public.subpart_results;
create policy "student inserts own subpart results" on public.subpart_results for insert with check (exists (select 1 from public.question_results qr join public.practice_attempts a on a.attempt_id=qr.attempt_id where qr.question_result_id=subpart_results.question_result_id and a.student_id=(select auth.uid())));
drop policy if exists "student updates own subpart results" on public.subpart_results;
create policy "student updates own subpart results" on public.subpart_results for update using (exists (select 1 from public.question_results qr join public.practice_attempts a on a.attempt_id=qr.attempt_id where qr.question_result_id=subpart_results.question_result_id and a.student_id=(select auth.uid()))) with check (exists (select 1 from public.question_results qr join public.practice_attempts a on a.attempt_id=qr.attempt_id where qr.question_result_id=subpart_results.question_result_id and a.student_id=(select auth.uid())));
