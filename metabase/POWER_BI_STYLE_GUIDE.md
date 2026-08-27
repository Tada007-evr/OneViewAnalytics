# OneView BI — Power BI-quality visual design guide

This guide makes the Metabase implementation visually consistent with the OneView Streamlit Overview dashboard and the Overview BRD/FSD MVP v1.6. Metabase should use the same Supabase semantic views as the student UI so numbers never diverge.

## Brand system

- Primary: `#5B35D5`
- Primary dark: `#3514A0`
- Text: `#211A4A`
- Muted text: `#6B7280`
- Canvas: `#F7F8FC`
- Card: `#FFFFFF`
- Grid/border: `#E8E8F1`
- Positive: `#12A66A`
- Warning: `#E49A27`
- Critical: `#D84B64`

Use white cards on a very light gray canvas, 12–16px visual corner radius where the BI platform supports it, restrained borders, generous white space, and minimal grid lines.

## Dashboard canvas

Desktop target: 1440px wide. Use a 12-column dashboard grid.

Header row:
- Student name
- Exam Level filter (AS Level / A Level)
- Last Updated
- Record Practice Paper link/action where embedding permits

Main content:
- Pure Mathematics section on the left six columns
- Statistics section on the right six columns
- identical visual structure for both subjects

## Visual hierarchy per subject

### Row A — KPI cards

1. Papers Completed / Target
2. Average Performance
3. Recent Score

Cards should have one primary number, a short supporting sentence, and no unnecessary chart chrome.

### Row B — advanced KPI visuals

4. Average Performance gauge
   - 0–100% scale
   - single accent bar
   - avoid speedometer styling with excessive color

5. Predicted Performance bullet/progress chart
   - predicted percentage as the main bar
   - recent score percentage as a reference marker
   - show `More data needed` instead of a zero bar when the prediction threshold is not met

### Row C — Target Practice

6. Completion donut
   - completed / target
   - central completion percentage
   - adjacent cards for Target, Available, Completed, Remaining and status

### Row D — analysis

7. Performance Trend
   - line chart with markers
   - last 8 attempts
   - y-axis fixed 0–100%
   - compact date x-axis
   - status displayed separately: Improving / Stable / Needs Focus / More data needed

8. Priority Improvement Areas
   - horizontal bar chart
   - top 3 only
   - sort by documented priority rank
   - conditional colors: High red, Medium amber, Monitor purple
   - tooltip: topic, subtopic, percentage, priority, observation count

### Row E — narrative cards

9. OneView Insight
10. Recommendation

Use the approved deterministic text from `v_overview_insight_recommendation`; do not recreate rule logic in Metabase.

## Filters

Dashboard filters:
- `student_id` — required, hidden from normal student-facing embedded use if identity is supplied by the application
- `academic_level` — prominent segmented/dropdown filter

Optional diagnostic BI filters:
- Subject
- Year
- Session
- Paper code
- Topic
- Subtopic

## Semantic sources

Use only these production views for Overview BI:

- `v_bi_overview_dashboard`
- `v_overview_attempts`
- `v_overview_priority_areas`
- `v_overview_subtopic_performance`
- `v_overview_insight_recommendation`

Do not reimplement Prediction V1, trend, target completion, priorities, Insight or Recommendation inside BI questions. Supabase is the semantic calculation layer.

## Interaction behaviour

- Exam Level refreshes every visual.
- Pure Mathematics and Statistics remain independent.
- Clicking a priority should link/drill to Topic Analysis where embedding supports URL parameters.
- Empty states must say `More data needed` or `Not Set`; never convert null analytical states to 0%.
- Tooltips should explain context without overwhelming the student.

## Power BI-quality principles

- Use visual hierarchy instead of many equally prominent charts.
- Keep one dominant message per card.
- Favor bullet charts, lines, horizontal ranking bars and donuts over dense tables.
- Keep percentages on a consistent 0–100 scale.
- Remove legends when the title already identifies a single series.
- Use direct labels for important last values.
- Use conditional color only where it communicates meaning.
- Keep charts aligned across the Pure Mathematics and Statistics columns.
- Avoid pie charts except the single Target Practice completion donut.
- Avoid 3D charts, rainbow palettes, excessive borders, and decorative gauges.

## Dashboard queries

Use `metabase/OVERVIEW_DASHBOARD_QUERIES.sql` as the source query pack. All KPI and analytical numbers must reconcile exactly to Streamlit for the same student and level.
