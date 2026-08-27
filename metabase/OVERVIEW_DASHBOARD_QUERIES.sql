-- OneView Overview Dashboard v1.6 — Metabase query pack
-- Bind {{student_id}} and {{academic_level}} as dashboard filters.

-- 1. Subject overview cards: returns Pure Mathematics + Statistics side by side.
select *
from public.v_bi_overview_dashboard
where student_id = {{student_id}}
  and academic_level = {{academic_level}}
order by case subject when 'Pure Mathematics' then 1 else 2 end;

-- 2. Pure Mathematics trend.
select attempt_date, percentage, paper_code
from public.v_overview_attempts
where student_id = {{student_id}}
  and academic_level = {{academic_level}}
  and subject = 'Pure Mathematics'
order by attempt_date;

-- 3. Statistics trend.
select attempt_date, percentage, paper_code
from public.v_overview_attempts
where student_id = {{student_id}}
  and academic_level = {{academic_level}}
  and subject = 'Statistics'
order by attempt_date;

-- 4. Top 3 priority areas.
select subject, priority_rank, topic_name, subtopic_name,
       average_percentage, priority, performance_gap_pp,
       recent_error_frequency, observation_count
from public.v_overview_priority_areas
where student_id = {{student_id}}
  and academic_level = {{academic_level}}
order by subject, priority_rank;

-- 5. Topic Analysis source.
select subject, topic_name, subtopic_name, observation_count,
       average_percentage, recent_error_frequency, subtopic_trend
from public.v_overview_subtopic_performance
where student_id = {{student_id}}
  and academic_level = {{academic_level}}
order by subject, average_percentage;
