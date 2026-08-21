-- DEMO DATA ONLY. Replace with verified Cambridge data.
insert into topics(topic_name,parent_topic) values
('Algebra','Pure Mathematics'),
('Functions','Pure Mathematics'),
('Coordinate Geometry','Pure Mathematics'),
('Trigonometry','Pure Mathematics'),
('Differentiation','Pure Mathematics')
on conflict (topic_name) do nothing;

insert into exam_papers(academic_level,subject,year,session,paper_code,total_marks)
values
('AS Level','Mathematics',2024,'May/June','DEMO-P1',75),
('AS Level','Mathematics',2024,'October/November','DEMO-P1',75)
on conflict(year,session,paper_code) do nothing;

do $$
declare
  p uuid;
  q uuid;
  t uuid;
begin
  select paper_id into p from exam_papers where year=2024 and session='May/June' and paper_code='DEMO-P1';
  select topic_id into t from topics where topic_name='Algebra';
  if not exists(select 1 from questions where paper_id=p and question_number='1') then
    insert into questions(paper_id,question_number,max_marks) values(p,'1',5) returning question_id into q;
    insert into question_topics values(q,t);
    insert into sub_parts(question_id,label,max_marks) values(q,'a',2),(q,'b',3);
  end if;

  select topic_id into t from topics where topic_name='Functions';
  if not exists(select 1 from questions where paper_id=p and question_number='2') then
    insert into questions(paper_id,question_number,max_marks) values(p,'2',5) returning question_id into q;
    insert into question_topics values(q,t);
  end if;
end $$;
