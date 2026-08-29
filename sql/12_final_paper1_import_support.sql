-- Practice Paper import support for FINAL_OneView_9709_Paper1_Mapping_Score.xlsx
-- Applied to production Supabase on 2026-08-29.

alter table public.question_results
  add column if not exists source_error_type text;

alter table public.subpart_results
  add column if not exists source_error_type text;

create table if not exists public.practice_error_type_mappings (
  source_error_type text primary key,
  normalized_error_type text not null check (
    normalized_error_type in (
      'No Error','Conceptual Error','Calculation Error','Careless Error',
      'Application Error','Misread Question','Incomplete Answer','Time Pressure',
      'Forgot Formula / Rule'
    )
  ),
  notes text,
  active boolean not null default true,
  updated_at timestamptz not null default now()
);

insert into public.practice_error_type_mappings(source_error_type, normalized_error_type, notes, active) values
('Incorrect formula','Forgot Formula / Rule','Legacy workbook label normalized to BRD controlled value.',true),
('Calclation error','Calculation Error','Legacy workbook spelling normalized to BRD controlled value.',true),
('Careless','Careless Error','Legacy workbook label normalized to BRD controlled value.',true),
('Missed step','Incomplete Answer','Legacy workbook label normalized to BRD controlled value.',true),
('Knowledge gap','Conceptual Error','Legacy workbook label normalized to BRD controlled value.',true),
('Simplification','Calculation Error','Legacy workbook label normalized to BRD controlled value.',true),
('Approximation','Calculation Error','Legacy workbook label normalized to BRD controlled value.',true),
('Content clarity','Conceptual Error','Legacy workbook label normalized to closest BRD controlled value; raw source retained in source_error_type.',true),
('Graph','Application Error','Legacy workbook label normalized to closest BRD controlled value; raw source retained in source_error_type.',true)
on conflict(source_error_type) do update set
  normalized_error_type = excluded.normalized_error_type,
  notes = excluded.notes,
  active = true,
  updated_at = now();
