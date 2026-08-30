-- OneView display-name alignment with finalized Overview/Record Practice prototypes.
-- Safe for the current project: resolves the student profile through the authenticated email.

update public.students s
set name = 'Laya Eshwarwak'
where s.student_id in (
    select u.id
    from auth.users u
    where lower(u.email) = lower('evreddy01@gmail.com')
);

select student_id, name, academic_level, subject
from public.students
where name = 'Laya Eshwarwak';
