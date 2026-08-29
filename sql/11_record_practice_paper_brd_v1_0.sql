-- OneView Record Practice Paper BRD + FSD implementation
-- Applies only to the Record Practice Paper capture model.

alter table public.question_results add column if not exists marks_lost numeric;
alter table public.subpart_results add column if not exists marks_lost numeric;

update public.question_results qr
set marks_lost = greatest(q.max_marks - qr.score, 0)
from public.questions q
where q.question_id = qr.question_id and qr.marks_lost is null;

update public.subpart_results sr
set marks_lost = greatest(sp.max_marks - sr.score, 0)
from public.sub_parts sp
where sp.sub_part_id = sr.sub_part_id and sr.marks_lost is null;

alter table public.question_results drop constraint if exists question_results_marks_lost_check;
alter table public.question_results add constraint question_results_marks_lost_check
check (marks_lost is null or (marks_lost >= 0 and marks_lost = trunc(marks_lost)));

alter table public.subpart_results drop constraint if exists subpart_results_marks_lost_check;
alter table public.subpart_results add constraint subpart_results_marks_lost_check
check (marks_lost is null or (marks_lost >= 0 and marks_lost = trunc(marks_lost)));

alter table public.question_results drop constraint if exists question_results_error_type_check;
alter table public.question_results add constraint question_results_error_type_check
check (error_type is null or error_type in ('No Error','Conceptual Error','Calculation Error','Careless Error','Application Error','Misread Question','Incomplete Answer','Time Pressure','Forgot Formula / Rule'));

alter table public.subpart_results drop constraint if exists subpart_results_error_type_check;
alter table public.subpart_results add constraint subpart_results_error_type_check
check (error_type is null or error_type in ('No Error','Conceptual Error','Calculation Error','Careless Error','Application Error','Misread Question','Incomplete Answer','Time Pressure','Forgot Formula / Rule'));

create unique index if not exists uq_practice_attempt_student_paper_completed
on public.practice_attempts(student_id,paper_id)
where status='completed';

create index if not exists idx_question_results_attempt_marks_lost on public.question_results(attempt_id,marks_lost);
create index if not exists idx_subpart_results_question_marks_lost on public.subpart_results(question_result_id,marks_lost);
