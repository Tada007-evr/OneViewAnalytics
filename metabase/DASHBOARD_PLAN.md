# OneView BI — Overview Dashboard v1.6

The attached **OneView Overview Dashboard BRD + FSD MVP v1.6** is the visual and functional source of truth for this dashboard. Metabase/BI must use the same Supabase semantic views as the Streamlit Overview page and must reproduce the BRD layout, hierarchy, wording, states, and subject independence. Do not substitute a different Power BI/Metabase-style page structure.

## Visual language

Match the approved OneView prototype:

- dark purple left navigation
- white dashboard cards on a pale neutral canvas
- dark navy text with purple accents
- compact rounded cards and restrained borders
- green positive/improving states
- amber/orange monitoring/on-track states
- red high-priority/needs-focus states
- no decorative gauge/donut/3-D/rainbow visual that is not required by the BRD

## Required navigation

Exactly:

- Overview
- Record Practice Paper
- Topic Analysis

Overview is highlighted when selected.

## Header

One top row with:

- Student name
- AS Level / A Level selector
- Last Updated
- `+ Record Practice Paper`

The selected level is the context filter for every Overview metric and visual.

## Main Overview layout

Two equal side-by-side subject panels:

- left: Pure Mathematics
- right: Statistics

Both panels must use the same card order and dimensions. Never combine subject results.

## Subject panel layout

### Heading

Show subject name/icon, Practice Target, Available Papers, and Edit Target.

### KPI row

Exactly three cards in this order:

1. Papers Completed / Target
2. Average Performance
3. Recent Score

Use runtime data. Use `More data needed` where an analytical metric is unavailable rather than presenting 0 as a performance result.

### Predicted Performance

One card below the KPI row, labelled exactly `Predicted Performance`. Display only a valid rule-based result from `v_bi_overview_dashboard`; otherwise show `More data needed`.

### Target Practice

Below the KPI/performance area show:

- Target Type
- Target
- Completed
- Remaining
- % Completion
- progress bar
- Status
- Available Papers
- level/subject context

`Edit Target` opens the target-setting popup in the student application. Minimum = 15; maximum = Available Papers.

### Analysis row

Left: Performance Trend line chart.

Right: Priority Improvement Areas, top 3 only.

Priority rows show Topic, Subtopic, Average %, and Priority. Use database rank and drill to Topic Analysis where embedding supports it.

### Narrative row

At the bottom of each subject panel:

- OneView Insight
- Recommendation

Use `v_overview_insight_recommendation` verbatim; do not recreate templates or free-form text in BI.

## Semantic sources

Use only the shared production semantic layer for Overview BI:

- `v_bi_overview_dashboard`
- `v_overview_attempts`
- `v_overview_priority_areas`
- `v_overview_subtopic_performance`
- `v_overview_insight_recommendation`

Do not recalculate Prediction V1, trend, completion, priority, Insight, or Recommendation inside Metabase.

## Empty-state rules

- Target not configured → `Not Set`
- No valid performance → `More data needed`
- Prediction insufficient → `More data needed`
- Trend below threshold → chart may show available attempts, but status is `More data needed`
- Fewer than 3 relevant subtopic observations → no weak priority classification
- No fabricated insight or recommendation

## Current data state

The verified database currently contains AS Level Pure Mathematics source data. Statistics and A Level must remain visible in the correct BRD positions but show runtime empty states until verified source data exists. Never populate prototype values as production data.

## BI build acceptance

The BI dashboard is accepted only when a screenshot at supported desktop resolution matches the BRD's overall structure and hierarchy: purple navigation, required header, two symmetric subject columns, three KPI cards, Predicted Performance, Target Practice, Trend + Priority, then Insight + Recommendation.

Connect Metabase Open Source to Supabase Postgres using Supabase Database connection credentials. Student-facing access must be restricted to the authorized student. The Streamlit application remains the primary student interface; Metabase is a secondary BI surface and must visually follow the same BRD standard.