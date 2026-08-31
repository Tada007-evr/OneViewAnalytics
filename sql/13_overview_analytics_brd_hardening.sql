-- OneView Overview analytics BRD/FSD hardening.
-- Aligns Prediction V1, trend, priority, insight and recommendation behaviour
-- with the finalized Overview BRD/FSD MVP v1.6.

insert into public.overview_analytics_config(config_key,config_value,description) values
 ('overall_min_completed_papers','5','Overall data sufficiency threshold before definitive priority/weakness analytics.'),
 ('no_priority_insight_text','"No priority area currently qualifies under the configured rules."','Configured neutral no-priority insight state allowed by BRD Section 23.'),
 ('no_priority_recommendation_text','"Continue regular practice; OneView will flag a priority when the configured rules qualify one."','Configured neutral no-priority recommendation state.')
on conflict(config_key) do update set config_value=excluded.config_value,description=excluded.description,updated_at=now();

-- Valid attempts only: completed, eligible paper, usable score/percentage and a valid mark scale.
create or replace view public.v_overview_attempts with(security_invoker=true) as
select a.attempt_id,a.student_id,a.paper_id,a.attempt_date,a.status,a.total_score,a.percentage,a.created_at,a.updated_at,p.academic_level,p.subject,p.paper_code,p.year,p.session,p.total_marks
from public.practice_attempts a join public.exam_papers p on p.paper_id=a.paper_id
where a.status='completed' and p.eligible=true and a.total_score is not null and a.percentage is not null and a.percentage between 0 and 100 and p.total_marks is not null and p.total_marks>0;

-- Prediction V1: configurable weights/minimum, normalized weights for an approved limited-data configuration.
create or replace view public.v_overview_prediction with(security_invoker=true) as
with cfg as (
 select coalesce((select config_value::text::integer from public.overview_analytics_config where config_key='prediction_min_attempts'),5) min_attempts,
        coalesce((select config_value from public.overview_analytics_config where config_key='prediction_v1_weights'),'[0.35,0.25,0.20,0.12,0.08]'::jsonb) weights
), weights as (
 select ordinality::integer rn,value::numeric weight from cfg cross join lateral jsonb_array_elements_text(cfg.weights) with ordinality
), r as (
 select oa.*,row_number() over(partition by student_id,academic_level,subject order by coalesce(updated_at,created_at) desc,attempt_date desc,attempt_id desc) rn from public.v_overview_attempts oa
), x as (
 select r.*,w.weight from r join weights w on w.rn=r.rn
), a as (
 select x.student_id,x.academic_level,x.subject,count(*)::integer attempt_count,sum(x.percentage*x.weight)::numeric weighted_sum,sum(x.weight)::numeric applied_weight_sum,
        max(x.total_marks) filter(where x.rn=1)::numeric(10,2) assessment_max_marks,(select min_attempts from cfg)::integer min_attempts,(select count(*) from weights)::integer full_weight_count
 from x group by x.student_id,x.academic_level,x.subject
), calc as (
 select a.*,case when attempt_count>=min_attempts and applied_weight_sum>0 then (weighted_sum/applied_weight_sum)::numeric(10,2) end predicted_percentage from a
)
select student_id,academic_level,subject,attempt_count,predicted_percentage,
       case when predicted_percentage is not null then (predicted_percentage/100*assessment_max_marks)::numeric(10,2) end predicted_score,
       case when predicted_percentage is not null then assessment_max_marks end predicted_max_marks,
       case when attempt_count<min_attempts then 'More data needed' when attempt_count<full_weight_count then 'Limited' else 'Sufficient' end prediction_state,
       case when attempt_count<min_attempts then null when attempt_count<full_weight_count then 'Limited' else 'Standard' end prediction_confidence
from calc;

-- Exact trend logic: latest two minus previous two, with configurable threshold and no definitive result <4 attempts.
create or replace view public.v_overview_trend with(security_invoker=true) as
with cfg as (
 select greatest(coalesce((select config_value::text::integer from public.overview_analytics_config where config_key='trend_min_attempts'),4),4) min_attempts,
        coalesce((select config_value::text::numeric from public.overview_analytics_config where config_key='trend_threshold_pp'),5::numeric) threshold_pp
), r as (
 select oa.*,row_number() over(partition by student_id,academic_level,subject order by coalesce(updated_at,created_at) desc,attempt_date desc,attempt_id desc) rn from public.v_overview_attempts oa
), a as (
 select student_id,academic_level,subject,count(*) filter(where rn<=4)::integer attempt_count,avg(percentage) filter(where rn in(1,2)) latest_two_avg,avg(percentage) filter(where rn in(3,4)) previous_two_avg from r group by student_id,academic_level,subject
)
select a.student_id,a.academic_level,a.subject,a.attempt_count,(a.latest_two_avg-a.previous_two_avg)::numeric(10,2) trend_delta_pp,
       case when a.attempt_count<(select min_attempts from cfg) then 'More data needed' when a.latest_two_avg-a.previous_two_avg>=(select threshold_pp from cfg) then 'Improving' when a.latest_two_avg-a.previous_two_avg<=-(select threshold_pp from cfg) then 'Needs Focus' else 'Stable' end trend_status
from a;

-- Topic/subtopic observations are built only from valid attempts and usable marked rows.
create or replace view public.v_overview_subtopic_attempts with(security_invoker=true) as
with mapped as(
 select oa.student_id,oa.academic_level,oa.subject,oa.attempt_id,oa.attempt_date,coalesce(oa.updated_at,oa.created_at) saved_at,t.topic_id,t.topic_name,st.subtopic_id,st.subtopic_name,qr.score,q.max_marks
 from public.question_results qr join public.v_overview_attempts oa on oa.attempt_id=qr.attempt_id join public.questions q on q.question_id=qr.question_id join public.question_topics qt on qt.question_id=q.question_id join public.topics t on t.topic_id=qt.topic_id left join public.subtopics st on st.subtopic_id=qt.subtopic_id
 where qr.score is not null and q.max_marks>0 and not exists(select 1 from public.sub_parts sp where sp.question_id=q.question_id)
 union all
 select oa.student_id,oa.academic_level,oa.subject,oa.attempt_id,oa.attempt_date,coalesce(oa.updated_at,oa.created_at),t.topic_id,t.topic_name,st.subtopic_id,st.subtopic_name,spr.score,sp.max_marks
 from public.subpart_results spr join public.question_results qr on qr.question_result_id=spr.question_result_id join public.v_overview_attempts oa on oa.attempt_id=qr.attempt_id join public.sub_parts sp on sp.sub_part_id=spr.sub_part_id join public.subpart_topics spt on spt.sub_part_id=sp.sub_part_id join public.topics t on t.topic_id=spt.topic_id left join public.subtopics st on st.subtopic_id=spt.subtopic_id
 where spr.score is not null and sp.max_marks>0
)
select student_id,academic_level,subject,attempt_id,attempt_date,saved_at,topic_id,topic_name,subtopic_id,coalesce(subtopic_name,'Unspecified') subtopic_name,sum(score) score,sum(max_marks) max_marks,
       case when sum(max_marks)>0 then sum(score)/sum(max_marks)*100 end attempt_percentage,bool_or(score<max_marks) error_flag
from mapped group by student_id,academic_level,subject,attempt_id,attempt_date,saved_at,topic_id,topic_name,subtopic_id,coalesce(subtopic_name,'Unspecified');

create or replace view public.v_overview_subtopic_performance with(security_invoker=true) as
with cfg as (select coalesce((select config_value::text::numeric from public.overview_analytics_config where config_key='trend_threshold_pp'),5::numeric) threshold_pp),
r as(select a.*,row_number() over(partition by student_id,academic_level,subject,topic_id,subtopic_id,subtopic_name order by saved_at desc,attempt_date desc,attempt_id desc) rn from public.v_overview_subtopic_attempts a),
a as(select student_id,academic_level,subject,topic_id,topic_name,subtopic_id,subtopic_name,count(*)::integer observation_count,avg(attempt_percentage)::numeric(10,2) average_percentage,
 count(*) filter(where rn<=4 and error_flag)::integer recent_error_count,count(*) filter(where rn<=4)::integer recent_observation_count,avg(attempt_percentage) filter(where rn in(1,2)) latest_two_avg,avg(attempt_percentage) filter(where rn in(3,4)) previous_two_avg from r group by student_id,academic_level,subject,topic_id,topic_name,subtopic_id,subtopic_name)
select a.*,case when recent_observation_count>0 then(recent_error_count::numeric/recent_observation_count*100)::numeric(10,2) else 0 end recent_error_frequency,
 case when observation_count<4 then 'More data needed' when latest_two_avg-previous_two_avg>=(select threshold_pp from cfg) then 'Improving' when latest_two_avg-previous_two_avg<=-(select threshold_pp from cfg) then 'Needs Focus' else 'Stable' end subtopic_trend from a;

-- Priority: overall sufficiency first, >=3 relevant observations, exact High/Medium/Monitor rules and tie-breaks.
create or replace view public.v_overview_priority_areas with(security_invoker=true) as
with cfg as (
 select coalesce((select config_value::text::integer from public.overview_analytics_config where config_key='priority_min_observations'),3) min_observations,
        coalesce((select config_value::text::integer from public.overview_analytics_config where config_key='overall_min_completed_papers'),5) overall_min_papers
), c as(
 select sp.*,m.average_percentage overall_subject_average,(m.average_percentage-sp.average_percentage)::numeric(10,2) performance_gap_pp,
        case when m.papers_completed<(select overall_min_papers from cfg) then null
             when sp.observation_count<(select min_observations from cfg) then null
             when m.average_percentage-sp.average_percentage>=15 then 'High'
             when m.average_percentage-sp.average_percentage>=10 and sp.recent_error_frequency>=50 then 'High'
             when m.average_percentage-sp.average_percentage>=5 and m.average_percentage-sp.average_percentage<15 then 'Medium'
             when m.average_percentage-sp.average_percentage>=0 and m.average_percentage-sp.average_percentage<5 then 'Monitor' else null end priority
 from public.v_overview_subtopic_performance sp join public.v_overview_subject_metrics m using(student_id,academic_level,subject)
), r as(
 select c.*,row_number() over(partition by student_id,academic_level,subject order by case priority when 'High' then 1 when 'Medium' then 2 when 'Monitor' then 3 else 9 end,performance_gap_pp desc,recent_error_frequency desc,observation_count desc,topic_name,subtopic_name) priority_rank from c where priority is not null
)
select * from r where priority_rank<=3;

-- Keep the original dashboard column order for compatibility; append confidence metadata at the end.
create or replace view public.v_bi_overview_dashboard with(security_invoker=true) as
select sc.student_id,sc.name,sc.academic_level,sc.subject,coalesce(i.available_papers,0) available_papers,t.target_type,t.target_value,coalesce(m.papers_completed,0) papers_completed,
 case when t.target_value is null then null else greatest(t.target_value-coalesce(m.papers_completed,0),0) end remaining,
 case when t.target_value is null or t.target_value=0 then null else least(coalesce(m.papers_completed,0)::numeric/t.target_value*100,100)::numeric(10,2) end completion_percentage,
 case when t.target_value is null then 'Not Set' when coalesce(m.papers_completed,0)::numeric/t.target_value*100>=100 then 'Target Achieved' when coalesce(m.papers_completed,0)::numeric/t.target_value*100>=75 then 'Ahead of Target' when coalesce(m.papers_completed,0)::numeric/t.target_value*100>=40 then 'On Track' else 'Behind Target' end target_status,
 m.average_score,m.average_percentage,m.recent_score,m.recent_max_marks,m.recent_percentage,m.recent_attempt_date,pr.predicted_score,pr.predicted_max_marks,pr.predicted_percentage,coalesce(pr.prediction_state,'More data needed') prediction_state,
 coalesce(tr.trend_status,'More data needed') trend_status,tr.trend_delta_pp,greatest(coalesce(m.last_attempt_update,'epoch'::timestamptz),coalesce(t.updated_at,'epoch'::timestamptz)) last_updated,
 pr.attempt_count prediction_attempt_count,pr.prediction_confidence
from public.v_overview_scope sc left join public.v_overview_inventory i using(academic_level,subject) left join public.student_practice_targets t using(student_id,academic_level,subject)
left join public.v_overview_subject_metrics m using(student_id,academic_level,subject) left join public.v_overview_prediction pr using(student_id,academic_level,subject) left join public.v_overview_trend tr using(student_id,academic_level,subject);

-- Insight/recommendation: deterministic approved precedence. Insufficient data blocks weakness claims.
-- A sufficient-data/no-priority case uses a configured neutral state rather than falsely claiming insufficiency.
create or replace view public.v_overview_insight_recommendation with (security_invoker=true) as
with cfg as (
 select coalesce((select config_value::text::integer from public.overview_analytics_config where config_key='overall_min_completed_papers'),5) overall_min_papers,
        trim(both '"' from coalesce((select config_value::text from public.overview_analytics_config where config_key='no_priority_insight_text'),'"No priority area currently qualifies under the configured rules."')) no_priority_insight,
        trim(both '"' from coalesce((select config_value::text from public.overview_analytics_config where config_key='no_priority_recommendation_text'),'"Continue regular practice; OneView will flag a priority when the configured rules qualify one."')) no_priority_recommendation
), top_priority as (select * from public.v_overview_priority_areas where priority_rank=1),
base as (select d.*,p.topic_name,p.subtopic_name,p.performance_gap_pp,p.recent_error_frequency,p.recent_error_count,p.recent_observation_count,p.subtopic_trend from public.v_bi_overview_dashboard d left join top_priority p using(student_id,academic_level,subject))
select student_id,name,academic_level,subject,
 case when papers_completed<(select overall_min_papers from cfg) then 'INS-05' when subtopic_name is null then 'NO-PRIORITY' when recent_error_frequency>=50 and recent_observation_count>=3 then 'INS-02' when subtopic_trend='Needs Focus' then 'INS-03' when performance_gap_pp>=5 then 'INS-01' when subtopic_trend='Improving' and performance_gap_pp>0 then 'INS-04' else 'NO-PRIORITY' end insight_rule_id,
 case when papers_completed<(select overall_min_papers from cfg) then 'More practice data is needed before OneView can reliably assess this area.' when subtopic_name is null then (select no_priority_insight from cfg) when recent_error_frequency>=50 and recent_observation_count>=3 then 'You have made errors in '||subtopic_name||' in '||recent_error_count||' of your last '||recent_observation_count||' relevant attempts.' when subtopic_trend='Needs Focus' then 'Your recent performance in '||subtopic_name||' is declining.' when performance_gap_pp>=5 then subtopic_name||' is below your overall performance.' when subtopic_trend='Improving' and performance_gap_pp>0 then 'Your performance in '||subtopic_name||' is improving, but it remains below your overall average.' else (select no_priority_insight from cfg) end insight_text,
 case when papers_completed<(select overall_min_papers from cfg) then 'REC-06' when subtopic_name is null then 'NO-PRIORITY' when recent_error_frequency>=50 and recent_observation_count>=3 then 'REC-02' when subtopic_trend='Needs Focus' then 'REC-03' when performance_gap_pp>=5 then 'REC-01' when subtopic_trend='Improving' and performance_gap_pp>0 then 'REC-05' else 'NO-PRIORITY' end recommendation_rule_id,
 case when papers_completed<(select overall_min_papers from cfg) then 'More relevant practice required; no weakness recommendation yet.' when subtopic_name is null then (select no_priority_recommendation from cfg) when recent_error_frequency>=50 and recent_observation_count>=3 then 'Review recent errors; practise the same skill; reattempt similar questions.' when subtopic_trend='Needs Focus' then 'Targeted practice before the next full paper; review mistakes afterward.' when performance_gap_pp>=5 then 'Review the concept; practise targeted questions; reattempt similar past-paper questions.' when subtopic_trend='Improving' and performance_gap_pp>0 then 'Continue targeted practice; reassess after more attempts.' else (select no_priority_recommendation from cfg) end recommendation_text
from base;

grant select on public.v_overview_attempts,public.v_overview_prediction,public.v_overview_trend,public.v_overview_subtopic_attempts,public.v_overview_subtopic_performance,public.v_overview_priority_areas,public.v_bi_overview_dashboard,public.v_overview_insight_recommendation to authenticated;
