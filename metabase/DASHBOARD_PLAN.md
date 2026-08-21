# Metabase dashboard build plan

## Connection

Add Supabase Postgres as a database in Metabase. Use the Postgres connection details from Supabase's Database > Connect screen.

Expose these views:

- `v_attempt_history`
- `v_question_performance`
- `v_topic_performance`
- `v_paper_progress`

## Dashboard 1 — Overview

1. Count rows in `v_attempt_history` → Papers completed
2. Average `percentage` → Average performance
3. Line chart: `attempt_date` vs `percentage`
4. Bar chart: `topic_name` vs `average_percentage`
5. Bar chart: `topic_name` vs `marks_lost`
6. Table: weakest topics ordered by marks lost descending

## Dashboard 2 — Topic Weakness

Filters:
- year
- session
- topic

Cards:
- Attempt count
- Available marks
- Score
- Marks lost
- Average %

Charts:
- Average % by topic
- Marks lost by topic
- Attempt count by topic

## Dashboard 3 — Paper Progress

Charts:
- completed papers by year/session
- percentage by attempt date
- score by paper code

## Dashboard 4 — Question Analysis

Use `v_question_performance`:
- average question %
- total marks lost by question
- question performance over time

## BI principle

Keep calculations in SQL views where possible so Streamlit and Metabase use the same definitions. This avoids dashboard numbers disagreeing with the student application.
