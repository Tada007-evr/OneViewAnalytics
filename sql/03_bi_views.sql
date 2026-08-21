-- OneView BI views. Security invoker keeps Supabase RLS applied to source tables.
create or replace view v_attempt_history with (security_invoker=true) as
select a.attempt_id,a.student_id,a.attempt_date,p.year,p.session,p.paper_code,a.total_score,p.total_marks,a.percentage
from practice_attempts a join exam_papers p on p.paper_id=a.paper_id where a.status='completed';

create or replace view v_question_performance with (security_invoker=true) as
select a.student_id,a.attempt_id,a.attempt_date,p.year,p.session,p.paper_code,q.question_id,q.question_number,q.max_marks,qr.score,q.max_marks-qr.score marks_lost,
case when q.max_marks>0 then qr.score/q.max_marks*100 end percentage
from question_results qr join practice_attempts a on a.attempt_id=qr.attempt_id join questions q on q.question_id=qr.question_id join exam_papers p on p.paper_id=q.paper_id where a.status='completed';

create or replace view v_topic_performance with (security_invoker=true) as
with mapped_scores as (
 select a.student_id,a.attempt_id,qt.topic_id,qr.score,q.max_marks
 from question_results qr join practice_attempts a on a.attempt_id=qr.attempt_id join questions q on q.question_id=qr.question_id join question_topics qt on qt.question_id=q.question_id
 where a.status='completed' and not exists(select 1 from sub_parts sp where sp.question_id=q.question_id)
 union all
 select a.student_id,a.attempt_id,st.topic_id,spr.score,sp.max_marks
 from subpart_results spr join question_results qr on qr.question_result_id=spr.question_result_id join practice_attempts a on a.attempt_id=qr.attempt_id join sub_parts sp on sp.sub_part_id=spr.sub_part_id join subpart_topics st on st.sub_part_id=sp.sub_part_id
 where a.status='completed')
select ms.student_id,t.topic_id,t.topic_name,count(distinct ms.attempt_id) attempt_count,sum(ms.max_marks) available_marks,sum(ms.score) score,sum(ms.max_marks-ms.score) marks_lost,
case when sum(ms.max_marks)>0 then sum(ms.score)/sum(ms.max_marks)*100 end average_percentage
from mapped_scores ms join topics t on t.topic_id=ms.topic_id group by ms.student_id,t.topic_id,t.topic_name;

create or replace view v_subtopic_performance with (security_invoker=true) as
with mapped_scores as (
 select a.student_id,a.attempt_id,qt.subtopic_id,qr.score,q.max_marks
 from question_results qr join practice_attempts a on a.attempt_id=qr.attempt_id join questions q on q.question_id=qr.question_id join question_topics qt on qt.question_id=q.question_id
 where a.status='completed' and not exists(select 1 from sub_parts sp where sp.question_id=q.question_id)
 union all
 select a.student_id,a.attempt_id,st.subtopic_id,spr.score,sp.max_marks
 from subpart_results spr join question_results qr on qr.question_result_id=spr.question_result_id join practice_attempts a on a.attempt_id=qr.attempt_id join sub_parts sp on sp.sub_part_id=spr.sub_part_id join subpart_topics st on st.sub_part_id=sp.sub_part_id
 where a.status='completed')
select ms.student_id,st.subtopic_id,st.subtopic_name,t.topic_name,count(distinct ms.attempt_id) attempt_count,sum(ms.max_marks) available_marks,sum(ms.score) score,sum(ms.max_marks-ms.score) marks_lost,
case when sum(ms.max_marks)>0 then sum(ms.score)/sum(ms.max_marks)*100 end average_percentage
from mapped_scores ms join subtopics st on st.subtopic_id=ms.subtopic_id join topics t on t.topic_id=st.topic_id group by ms.student_id,st.subtopic_id,st.subtopic_name,t.topic_name;

create or replace view v_paper_progress with (security_invoker=true) as
select student_id,year,session,count(*) completed_papers,avg(percentage) average_percentage
from v_attempt_history group by student_id,year,session;

create or replace view v_student_readiness with (security_invoker=true) as
select student_id,count(*) papers_completed,avg(percentage) average_percentage,max(percentage) best_percentage,
(array_agg(percentage order by attempt_date desc))[1] latest_percentage,
avg(percentage) filter(where attempt_date>=current_date-interval '30 days') recent_30_day_percentage
from v_attempt_history group by student_id;
