-- Deterministic Overview Insight + Recommendation view for Streamlit/Metabase parity.
create or replace view public.v_overview_insight_recommendation with (security_invoker=true) as
with top_priority as (select * from public.v_overview_priority_areas where priority_rank=1),
base as (
 select d.*,p.topic_name,p.subtopic_name,p.performance_gap_pp,p.recent_error_frequency,p.recent_error_count,p.recent_observation_count,p.subtopic_trend
 from public.v_bi_overview_dashboard d left join top_priority p using(student_id,academic_level,subject)
)
select student_id,name,academic_level,subject,
 case when papers_completed<5 then 'INS-05' when subtopic_name is null then null when recent_error_frequency>=50 then 'INS-02' when subtopic_trend='Needs Focus' then 'INS-03' when performance_gap_pp>=5 then 'INS-01' when subtopic_trend='Improving' and performance_gap_pp>0 then 'INS-04' end insight_rule_id,
 case when papers_completed<5 then 'More practice data is needed before OneView can reliably assess this area.' when subtopic_name is null then null when recent_error_frequency>=50 then 'You have made errors in '||subtopic_name||' in '||recent_error_count||' of your last '||recent_observation_count||' relevant attempts.' when subtopic_trend='Needs Focus' then 'Your recent performance in '||subtopic_name||' is declining.' when performance_gap_pp>=5 then subtopic_name||' is below your overall performance.' when subtopic_trend='Improving' and performance_gap_pp>0 then 'Your performance in '||subtopic_name||' is improving, but it remains below your overall average.' end insight_text,
 case when papers_completed<5 then 'REC-06' when subtopic_name is null then null when recent_error_frequency>=50 then 'REC-02' when subtopic_trend='Needs Focus' then 'REC-03' when performance_gap_pp>=5 then 'REC-01' when subtopic_trend='Improving' and performance_gap_pp>0 then 'REC-05' end recommendation_rule_id,
 case when papers_completed<5 then 'More relevant practice required; no weakness recommendation yet.' when subtopic_name is null then null when recent_error_frequency>=50 then 'Review recent errors; practise the same skill; reattempt similar questions.' when subtopic_trend='Needs Focus' then 'Targeted practice before the next full paper; review mistakes afterward.' when performance_gap_pp>=5 then 'Review the concept; practise targeted questions; reattempt similar past-paper questions.' when subtopic_trend='Improving' and performance_gap_pp>0 then 'Continue targeted practice; reassess after more attempts.' end recommendation_text
from base;
grant select on public.v_overview_insight_recommendation to authenticated;
