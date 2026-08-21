-- Add source/practice annotations from the workbook to existing result tables.
alter table question_results add column if not exists error_type text;
alter table question_results add column if not exists verified text;
alter table subpart_results add column if not exists error_type text;
alter table subpart_results add column if not exists verified text;
