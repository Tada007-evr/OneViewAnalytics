-- Post-load validation for FINAL_OneView_9709_Paper1_Mapping_Score.xlsx

select 'topics' item,count(*) value from public.topics
union all select 'subtopics',count(*) from public.subtopics
union all select 'papers',count(*) from public.exam_papers
union all select 'questions',count(*) from public.questions
union all select 'subparts',count(*) from public.sub_parts
union all select 'question_topics',count(*) from public.question_topics
union all select 'subpart_topics',count(*) from public.subpart_topics
union all select 'attempts',count(*) from public.practice_attempts
union all select 'question_results',count(*) from public.question_results
union all select 'subpart_results',count(*) from public.subpart_results;

select ep.session, ep.paper_code, ep.total_marks, pa.attempt_date, pa.total_score, pa.percentage
from public.exam_papers ep
join public.practice_attempts pa on pa.paper_id=ep.paper_id
order by ep.year, ep.session, ep.paper_code;

select count(*) as null_question_subtopic_mappings
from public.question_topics where subtopic_id is null;

select count(*) as null_subpart_subtopic_mappings
from public.subpart_topics where subtopic_id is null;

select count(*) as invalid_question_scores
from public.question_results qr
join public.questions q on q.question_id=qr.question_id
where qr.score < 0 or qr.score > q.max_marks;

select count(*) as invalid_subpart_scores
from public.subpart_results sr
join public.sub_parts sp on sp.sub_part_id=sr.sub_part_id
where sr.score < 0 or sr.score > sp.max_marks;

select count(*) as duplicate_completed_attempts
from (
  select student_id,paper_id,count(*) c
  from public.practice_attempts
  where status='completed'
  group by student_id,paper_id
  having count(*) > 1
) x;

select count(*) as uncontrolled_error_types
from (
  select error_type from public.question_results
  union all
  select error_type from public.subpart_results
) x
where error_type is not null
  and error_type not in (
    'No Error','Conceptual Error','Calculation Error','Careless Error',
    'Application Error','Misread Question','Incomplete Answer','Time Pressure',
    'Forgot Formula / Rule'
  );
