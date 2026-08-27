# OneView Overview Dashboard — MVP v1.6 implementation

This implementation is based on the supplied **OneView Overview Dashboard BRD + FSD MVP v1.6 / Edit Target Requirements**.

## Supabase: where to view the data and BI layer

Open the OneViewAnalytics Supabase project and use **Table Editor** / **Database**.

### Application tables

- `students`
- `exam_papers`
- `questions`
- `sub_parts`
- `topics`
- `subtopics`
- `practice_attempts`
- `question_results`
- `subpart_results`
- `student_practice_targets`
- `overview_target_presets`
- `overview_analytics_config`

### BI / semantic views

- `v_bi_overview_dashboard` — one row per student + exam level + subject; planning, average, recent, prediction, trend, last updated
- `v_overview_attempts` — eligible completed attempts scoped by level and subject
- `v_overview_subject_metrics` — average/recent performance
- `v_overview_prediction` — Prediction V1 using 35/25/20/12/8 weights; definitive only at 5+ valid attempts
- `v_overview_trend` — exact latest-2 versus previous-2 ±5 percentage-point rule
- `v_overview_subtopic_attempts` — per-attempt topic/subtopic evidence
- `v_overview_subtopic_performance` — shared Topic Analysis metrics
- `v_overview_priority_areas` — top 3 High/Medium/Monitor priorities using the documented gap, repeated-error and tie-break rules

These views are what the Streamlit Overview and the Metabase query pack use, preventing UI and BI calculation drift.

## Current verified data

The existing verified inventory contains **AS Level / Pure Mathematics / Paper 1** data. It does not contain verified Statistics or A Level inventory, so those panels intentionally show no available papers / more-data-needed states rather than fabricated values.

## Target Practice

Targets are independent by Student + Exam Level + Subject. The final Edit Target requirement is enforced at the database level:

- minimum target = 15 papers
- maximum target = Available Papers
- Available Papers is shown in the Edit Target dialog
- changing a target never edits historical attempts

Because the current verified Pure Mathematics inventory contains fewer than 15 eligible papers, the UI correctly explains that a target cannot yet be saved for that scope. When verified inventory reaches 15+, the dialog automatically enables valid presets/custom values.

## Visual dashboard

The Streamlit Overview page is the primary student BI dashboard and follows the supplied prototype: deep-purple navigation, white rounded panels, Pure Mathematics and Statistics side-by-side, KPI cards, Predicted Performance, Target Practice, performance trend, priority improvement areas, OneView Insight and Recommendation.

The Metabase assets under `/metabase` use the same semantic views and specify the same OneView color/style language for secondary BI/exploration.

## Deployment

Streamlit Community Cloud should redeploy automatically from `main`. The app entry point remains `app/main.py`. No new Streamlit secrets are required beyond `SUPABASE_URL` and `SUPABASE_ANON_KEY`.
