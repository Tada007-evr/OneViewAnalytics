# OneView BI — Overview Dashboard v1.6

The BI layer must use the same Supabase views as the Streamlit Overview page. Do not recreate formulas in Metabase. The authoritative semantic views are `v_bi_overview_dashboard`, `v_overview_attempts`, `v_overview_priority_areas`, and `v_overview_subtopic_performance`.

## Visual language

Match the approved OneView prototype: deep purple navigation/branding (`#3514A0` / `#5B35D5`), white cards, pale grey page background (`#F7F8FC`), dark navy text (`#211A4A`), rounded cards, green positive states, amber monitoring states, and red priority/needs-focus states. Keep Pure Mathematics and Statistics side-by-side and never combine their scores.

## Required filters

- Student ID (locked to the authorized student when embedded)
- Exam Level: `AS Level` / `A Level`
- Subject panels: `Pure Mathematics` and `Statistics` remain independent

## Overview cards per subject

Source: `v_bi_overview_dashboard`.

- Available Papers
- Practice Target
- Papers Completed
- Remaining
- Completion % and Target Status
- Average Performance
- Recent Score
- Predicted Performance (only when `prediction_state = 'Sufficient'`)
- Trend Status
- Last Updated

## Trend

Source: `v_overview_attempts`. Line chart: `attempt_date` vs `percentage`, filtered to student + level + subject. Use the same purple line used by Streamlit.

## Priority Improvement Areas

Source: `v_overview_priority_areas`. Show only `priority_rank <= 3`. Columns: Topic, Subtopic, Average %, Priority. Priority is rule-based and must not be replaced by marks-lost ranking.

## Topic Analysis

Source: `v_overview_subtopic_performance`. Use the same average %, observation count, recent error frequency, and trend fields as the application.

## Empty-state rules

Do not display zero as a performance result when data is insufficient. Use `More data needed` / blank visual states for prediction, trend, priority, insight and recommendation according to the BRD.

## Important current-data state

The verified database currently contains AS Level Pure Mathematics Paper 1 data. Statistics and A Level panels must remain visible but empty until verified source data is loaded. Do not fabricate inventory, scores or targets.

## Connection

Connect Metabase Open Source to the Supabase Postgres database using Supabase **Database → Connect** credentials. Set the collection/dashboard permissions so student-facing embedded BI is filtered to the authenticated student. For the visual student product, Streamlit is the primary dashboard and already implements the prototype look and feel; Metabase is the secondary BI/exploration surface using the same views.
