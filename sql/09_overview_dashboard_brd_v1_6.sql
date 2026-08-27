-- OneView Overview Dashboard BRD + FSD MVP v1.6
-- Applied to production Supabase on 27 Aug 2026.
-- Existing 9709/1x papers are classified as AS Level / Pure Mathematics.
-- No Statistics or A Level paper records are fabricated when source data is absent.

alter table public.exam_papers add column if not exists eligible boolean not null default true;
update public.exam_papers set subject=case when paper_code like '9709/1%' then 'Pure Mathematics' when paper_code like '9709/5%' then 'Statistics' else subject end;

create table if not exists public.student_practice_targets (
 target_id uuid primary key default gen_random_uuid(), student_id uuid not null references public.students(student_id) on delete cascade,
 academic_level text not null check(academic_level in ('AS Level','A Level')),
 subject text not null check(subject in ('Pure Mathematics','Statistics')),
 target_type text not null check(target_type in ('Beginner','Recommended','Intensive','Custom')),
 target_value integer not null check(target_value>=15), created_at timestamptz not null default now(), updated_at timestamptz not null default now(),
 unique(student_id,academic_level,subject));

create table if not exists public.overview_target_presets (
 academic_level text not null, subject text not null, target_type text not null, target_value integer not null check(target_value>=15), active boolean not null default true,
 primary key(academic_level,subject,target_type));
insert into public.overview_target_presets values
 ('AS Level','Pure Mathematics','Beginner',15,true),('AS Level','Pure Mathematics','Recommended',25,true),('AS Level','Pure Mathematics','Intensive',35,true),
 ('AS Level','Statistics','Beginner',15,true),('AS Level','Statistics','Recommended',25,true),('AS Level','Statistics','Intensive',35,true),
 ('A Level','Pure Mathematics','Beginner',20,true),('A Level','Pure Mathematics','Recommended',30,true),('A Level','Pure Mathematics','Intensive',40,true),
 ('A Level','Statistics','Beginner',15,true),('A Level','Statistics','Recommended',20,true),('A Level','Statistics','Intensive',30,true)
on conflict(academic_level,subject,target_type) do update set target_value=excluded.target_value,active=true;

create table if not exists public.overview_analytics_config(config_key text primary key,config_value jsonb not null,description text,updated_at timestamptz not null default now());
insert into public.overview_analytics_config(config_key,config_value,description) values
 ('prediction_v1_weights','[0.35,0.25,0.20,0.12,0.08]','Most recent to fifth most recent valid attempt.'),
 ('prediction_min_attempts','5','Minimum for definitive Predicted Performance.'),('trend_min_attempts','4','Minimum for definitive trend.'),
 ('priority_min_observations','3','Minimum relevant observations before priority.'),('trend_threshold_pp','5','Trend threshold percentage points.'),
 ('target_minimum','15','Final Edit Target MVP minimum.')
on conflict(config_key) do update set config_value=excluded.config_value,description=excluded.description,updated_at=now();

alter table public.student_practice_targets enable row level security;
alter table public.overview_target_presets enable row level security;
alter table public.overview_analytics_config enable row level security;
drop policy if exists "student reads own targets" on public.student_practice_targets;
create policy "student reads own targets" on public.student_practice_targets for select to authenticated using(student_id=(select auth.uid()));
drop policy if exists "student inserts own targets" on public.student_practice_targets;
create policy "student inserts own targets" on public.student_practice_targets for insert to authenticated with check(student_id=(select auth.uid()));
drop policy if exists "student updates own targets" on public.student_practice_targets;
create policy "student updates own targets" on public.student_practice_targets for update to authenticated using(student_id=(select auth.uid())) with check(student_id=(select auth.uid()));
drop policy if exists "authenticated reads target presets" on public.overview_target_presets;
create policy "authenticated reads target presets" on public.overview_target_presets for select to authenticated using(true);
drop policy if exists "authenticated reads overview config" on public.overview_analytics_config;
create policy "authenticated reads overview config" on public.overview_analytics_config for select to authenticated using(true);
grant select,insert,update on public.student_practice_targets to authenticated;
grant select on public.overview_target_presets,public.overview_analytics_config to authenticated;

create or replace function public.validate_student_practice_target() returns trigger language plpgsql security invoker set search_path=public as $$
declare available_count integer;
begin
 select count(*) into available_count from public.exam_papers where eligible=true and academic_level=new.academic_level and subject=new.subject;
 if new.target_value<15 then raise exception 'Practice target must be at least 15 papers.'; end if;
 if new.target_value>available_count then raise exception 'Practice target (%) cannot exceed Available Papers (%).',new.target_value,available_count; end if;
 new.updated_at=now(); return new;
end $$;
drop trigger if exists trg_validate_student_practice_target on public.student_practice_targets;
create trigger trg_validate_student_practice_target before insert or update on public.student_practice_targets for each row execute function public.validate_student_practice_target();
create index if not exists idx_targets_student_scope on public.student_practice_targets(student_id,academic_level,subject);
create index if not exists idx_exam_papers_overview_scope on public.exam_papers(academic_level,subject,eligible);
create index if not exists idx_attempts_student_date on public.practice_attempts(student_id,attempt_date desc,updated_at desc);

create or replace view public.v_overview_scope with(security_invoker=true) as
select s.student_id,s.name,l.academic_level,x.subject from public.students s cross join(values('AS Level'::text),('A Level'::text))l(academic_level) cross join(values('Pure Mathematics'::text),('Statistics'::text))x(subject);
create or replace view public.v_overview_inventory with(security_invoker=true) as select academic_level,subject,count(*)::integer available_papers from public.exam_papers where eligible=true group by academic_level,subject;
create or replace view public.v_overview_attempts with(security_invoker=true) as
select a.attempt_id,a.student_id,a.paper_id,a.attempt_date,a.status,a.total_score,a.percentage,a.created_at,a.updated_at,p.academic_level,p.subject,p.paper_code,p.year,p.session,p.total_marks
from public.practice_attempts a join public.exam_papers p on p.paper_id=a.paper_id where a.status='completed' and p.eligible=true;

create or replace view public.v_overview_subject_metrics with(security_invoker=true) as
with r as(select oa.*,row_number() over(partition by student_id,academic_level,subject order by coalesce(updated_at,created_at) desc,attempt_date desc,attempt_id desc) rn from public.v_overview_attempts oa)
select student_id,academic_level,subject,count(*)::integer papers_completed,avg(total_score)::numeric(10,2) average_score,avg(percentage)::numeric(10,2) average_percentage,
 max(total_score) filter(where rn=1)::numeric(10,2) recent_score,max(total_marks) filter(where rn=1)::numeric(10,2) recent_max_marks,max(percentage) filter(where rn=1)::numeric(10,2) recent_percentage,
 max(attempt_date) recent_attempt_date,max(coalesce(updated_at,created_at)) last_attempt_update from r group by student_id,academic_level,subject;

create or replace view public.v_overview_prediction with(security_invoker=true) as
with r as(select oa.*,row_number() over(partition by student_id,academic_level,subject order by coalesce(updated_at,created_at) desc,attempt_date desc,attempt_id desc) rn from public.v_overview_attempts oa),
 x as(select *,case rn when 1 then .35 when 2 then .25 when 3 then .20 when 4 then .12 when 5 then .08 end weight from r where rn<=5),
 a as(select student_id,academic_level,subject,count(*)::integer attempt_count,sum(percentage*weight)::numeric(10,4) weighted_percentage,max(total_marks) filter(where rn=1)::numeric(10,2) assessment_max_marks from x group by student_id,academic_level,subject)
select student_id,academic_level,subject,attempt_count,case when attempt_count>=5 then weighted_percentage::numeric(10,2) end predicted_percentage,
 case when attempt_count>=5 then(weighted_percentage/100*assessment_max_marks)::numeric(10,2) end predicted_score,case when attempt_count>=5 then assessment_max_marks end predicted_max_marks,
 case when attempt_count>=5 then 'Sufficient' else 'More data needed' end prediction_state from a;

create or replace view public.v_overview_trend with(security_invoker=true) as
with r as(select oa.*,row_number() over(partition by student_id,academic_level,subject order by coalesce(updated_at,created_at) desc,attempt_date desc,attempt_id desc) rn from public.v_overview_attempts oa),
 a as(select student_id,academic_level,subject,count(*) filter(where rn<=4)::integer attempt_count,avg(percentage) filter(where rn in(1,2)) latest_two_avg,avg(percentage) filter(where rn in(3,4)) previous_two_avg from r group by student_id,academic_level,subject)
select student_id,academic_level,subject,attempt_count,(latest_two_avg-previous_two_avg)::numeric(10,2) trend_delta_pp,
 case when attempt_count<4 then 'More data needed' when latest_two_avg-previous_two_avg>=5 then 'Improving' when latest_two_avg-previous_two_avg<=-5 then 'Needs Focus' else 'Stable' end trend_status from a;

create or replace view public.v_overview_subtopic_attempts with(security_invoker=true) as
with mapped as(
 select oa.student_id,oa.academic_level,oa.subject,oa.attempt_id,oa.attempt_date,coalesce(oa.updated_at,oa.created_at) saved_at,t.topic_id,t.topic_name,st.subtopic_id,st.subtopic_name,qr.score,q.max_marks
 from public.question_results qr join public.v_overview_attempts oa on oa.attempt_id=qr.attempt_id join public.questions q on q.question_id=qr.question_id join public.question_topics qt on qt.question_id=q.question_id join public.topics t on t.topic_id=qt.topic_id left join public.subtopics st on st.subtopic_id=qt.subtopic_id
 where not exists(select 1 from public.sub_parts sp where sp.question_id=q.question_id)
 union all
 select oa.student_id,oa.academic_level,oa.subject,oa.attempt_id,oa.attempt_date,coalesce(oa.updated_at,oa.created_at),t.topic_id,t.topic_name,st.subtopic_id,st.subtopic_name,spr.score,sp.max_marks
 from public.subpart_results spr join public.question_results qr on qr.question_result_id=spr.question_result_id join public.v_overview_attempts oa on oa.attempt_id=qr.attempt_id join public.sub_parts sp on sp.sub_part_id=spr.sub_part_id join public.subpart_topics spt on spt.sub_part_id=sp.sub_part_id join public.topics t on t.topic_id=spt.topic_id left join public.subtopics st on st.subtopic_id=spt.subtopic_id)
select student_id,academic_level,subject,attempt_id,attempt_date,saved_at,topic_id,topic_name,subtopic_id,coalesce(subtopic_name,'Unspecified') subtopic_name,sum(score) score,sum(max_marks) max_marks,
 case when sum(max_marks)>0 then sum(score)/sum(max_marks)*100 end attempt_percentage,bool_or(score<max_marks) error_flag
from mapped group by student_id,academic_level,subject,attempt_id,attempt_date,saved_at,topic_id,topic_name,subtopic_id,coalesce(subtopic_name,'Unspecified');

create or replace view public.v_overview_subtopic_performance with(security_invoker=true) as
with r as(select a.*,row_number() over(partition by student_id,academic_level,subject,topic_id,subtopic_id,subtopic_name order by saved_at desc,attempt_date desc,attempt_id desc) rn from public.v_overview_subtopic_attempts a),
 a as(select student_id,academic_level,subject,topic_id,topic_name,subtopic_id,subtopic_name,count(*)::integer observation_count,avg(attempt_percentage)::numeric(10,2) average_percentage,
 count(*) filter(where rn<=4 and error_flag)::integer recent_error_count,count(*) filter(where rn<=4)::integer recent_observation_count,avg(attempt_percentage) filter(where rn in(1,2)) latest_two_avg,avg(attempt_percentage) filter(where rn in(3,4)) previous_two_avg from r group by student_id,academic_level,subject,topic_id,topic_name,subtopic_id,subtopic_name)
select a.*,case when recent_observation_count>0 then(recent_error_count::numeric/recent_observation_count*100)::numeric(10,2) else 0 end recent_error_frequency,
 case when observation_count<4 then 'More data needed' when latest_two_avg-previous_two_avg>=5 then 'Improving' when latest_two_avg-previous_two_avg<=-5 then 'Needs Focus' else 'Stable' end subtopic_trend from a;

create or replace view public.v_overview_priority_areas with(security_invoker=true) as
with c as(select sp.*,m.average_percentage overall_subject_average,(m.average_percentage-sp.average_percentage)::numeric(10,2) performance_gap_pp,
 case when sp.observation_count<3 then null when m.average_percentage-sp.average_percentage>=15 then 'High' when m.average_percentage-sp.average_percentage>=10 and sp.recent_error_frequency>=50 then 'High'
 when m.average_percentage-sp.average_percentage>=5 and m.average_percentage-sp.average_percentage<15 then 'Medium' when m.average_percentage-sp.average_percentage>=0 and m.average_percentage-sp.average_percentage<5 then 'Monitor' else null end priority
 from public.v_overview_subtopic_performance sp join public.v_overview_subject_metrics m using(student_id,academic_level,subject)),
 r as(select c.*,row_number() over(partition by student_id,academic_level,subject order by case priority when 'High' then 1 when 'Medium' then 2 when 'Monitor' then 3 else 9 end,performance_gap_pp desc,recent_error_frequency desc,observation_count desc,topic_name,subtopic_name) priority_rank from c where priority is not null)
select * from r where priority_rank<=3;

create or replace view public.v_bi_overview_dashboard with(security_invoker=true) as
select sc.student_id,sc.name,sc.academic_level,sc.subject,coalesce(i.available_papers,0) available_papers,t.target_type,t.target_value,coalesce(m.papers_completed,0) papers_completed,
 case when t.target_value is null then null else greatest(t.target_value-coalesce(m.papers_completed,0),0) end remaining,
 case when t.target_value is null or t.target_value=0 then null else least(coalesce(m.papers_completed,0)::numeric/t.target_value*100,100)::numeric(10,2) end completion_percentage,
 case when t.target_value is null then 'Not Set' when coalesce(m.papers_completed,0)::numeric/t.target_value*100>=100 then 'Target Achieved' when coalesce(m.papers_completed,0)::numeric/t.target_value*100>=75 then 'Ahead of Target' when coalesce(m.papers_completed,0)::numeric/t.target_value*100>=40 then 'On Track' else 'Behind Target' end target_status,
 m.average_score,m.average_percentage,m.recent_score,m.recent_max_marks,m.recent_percentage,m.recent_attempt_date,pr.predicted_score,pr.predicted_max_marks,pr.predicted_percentage,coalesce(pr.prediction_state,'More data needed') prediction_state,
 coalesce(tr.trend_status,'More data needed') trend_status,tr.trend_delta_pp,greatest(coalesce(m.last_attempt_update,'epoch'::timestamptz),coalesce(t.updated_at,'epoch'::timestamptz)) last_updated
from public.v_overview_scope sc left join public.v_overview_inventory i using(academic_level,subject) left join public.student_practice_targets t using(student_id,academic_level,subject)
left join public.v_overview_subject_metrics m using(student_id,academic_level,subject) left join public.v_overview_prediction pr using(student_id,academic_level,subject) left join public.v_overview_trend tr using(student_id,academic_level,subject);

grant select on public.v_overview_scope,public.v_overview_inventory,public.v_overview_attempts,public.v_overview_subject_metrics,public.v_overview_prediction,public.v_overview_trend,public.v_overview_subtopic_attempts,public.v_overview_subtopic_performance,public.v_overview_priority_areas,public.v_bi_overview_dashboard to authenticated;
