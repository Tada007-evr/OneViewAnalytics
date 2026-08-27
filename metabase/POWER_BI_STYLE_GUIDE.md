# OneView BI — BRD visual implementation standard

This document is the authoritative visual standard for the OneView BI dashboard. The attached **OneView Overview Dashboard BRD + FSD MVP v1.6** is the source of truth. BI must reproduce the BRD prototype's layout, hierarchy, wording, states, and interaction intent. Do not replace the BRD design with generic Power BI, Metabase, or dashboard conventions when they conflict with the prototype.

## 1. Non-negotiable visual principle

The BI Overview must look and behave like the BRD Overview prototype:

- deep purple OneView left navigation
- white main dashboard canvas on a very light neutral background
- student name at the top
- AS Level / A Level selector at the top, never in left navigation
- Last updated timestamp at the top
- prominent `+ Record Practice Paper` action
- Pure Mathematics on the left and Statistics on the right
- both subject panels use the same structure and visual hierarchy
- compact purple-accented cards, restrained borders, rounded corners, dark navy text
- green for positive/improving states, amber/orange for monitoring/on-track states, red for high-priority/needs-focus states
- no decorative visual that is not present in, or directly required by, the BRD

Do **not** add speedometer gauges, decorative donuts, 3-D charts, rainbow palettes, unrelated KPI visuals, or extra navigation simply to make the dashboard look more like another BI product.

## 2. Required page structure

Use a desktop/laptop layout matching Figure 1 of the BRD.

### Left navigation

Exactly these MVP destinations:

1. Overview — highlighted when selected
2. Record Practice Paper
3. Topic Analysis

Student identity/logout remains at the bottom of the navigation area where supported.

### Header

One horizontal header row containing:

- Student name
- `AS Level | A Level` selector
- Last updated timestamp
- `+ Record Practice Paper` action

The selected level filters **every** visual and metric on the Overview.

### Subject panels

Use two equal-width side-by-side panels:

- Left: `PURE MATHEMATICS`
- Right: `STATISTICS`

Never combine the subjects into a total score or blended performance metric.

## 3. Exact visual hierarchy inside each subject panel

### Subject heading row

Show:

- subject icon/name
- `Practice Target: <value> papers`
- `Available Papers: <value>`
- `Edit Target` action

If target is not configured, display `Not Set` rather than assuming a default.

### KPI row

Exactly three primary KPI cards:

1. `PAPERS COMPLETED`
   - main value: Completed / Target
   - supporting value: completion percentage when target exists

2. `AVERAGE PERFORMANCE`
   - main value: average score/marks where available
   - supporting value: average percentage
   - use `More data needed` rather than a fake 0 when no valid attempt exists

3. `RECENT SCORE`
   - main value: most recent valid score / relevant maximum marks
   - supporting value: recent percentage
   - use `More data needed` where appropriate

### Predicted Performance

A single compact card below the KPI row labelled exactly:

`PREDICTED PERFORMANCE`

Do not display `Prediction V1` as a user-facing label.

When sufficient data exists, show the runtime-derived predicted score/percentage. When insufficient, show `More data needed`. Do not show a zero prediction.

### Target Practice panel

Display within Overview below the KPI/performance area, consistent with Figure 2.

Show:

- Target Type
- Target
- Completed
- Remaining
- % Completion
- progress bar
- Status
- Available Papers
- selected Level + Subject context
- target explanation/info tooltip

Status labels:

- 0–39% `Behind Target`
- 40–74% `On Track`
- 75–99% `Ahead of Target`
- 100% `Target Achieved`

The panel is planning-only and must not visually imply academic readiness.

### Analysis row

Left half:

`PERFORMANCE TREND`

- compact line chart
- percentage y-axis
- valid recent attempts only
- selected student + level + subject only
- status: Improving / Stable / Needs Focus / More data needed
- chart may still show available attempts even if the minimum trend threshold is not met

Right half:

`PRIORITY IMPROVEMENT AREAS`

- top 3 only
- each row shows Topic, Subtopic, performance %, and Priority
- priorities: High / Medium / Monitor
- ranked according to the database rule engine, not marks-lost sorting
- clickable/drill-through to Topic Analysis where the BI platform supports it
- if fewer than 3 priorities qualify, show only those available
- if none qualifies because of insufficient data, show `More data needed`

### Bottom narrative row

Two equal cards:

- `ONEVIEW INSIGHT`
- `RECOMMENDATION`

Use only deterministic text supplied by `v_overview_insight_recommendation`. Do not generate alternative wording in BI.

## 4. Edit Target popup

The BI/embedded application must retain the BRD Edit Target behaviour:

- Trigger: `Edit Target`
- Action: popup/modal
- show Available Papers inside popup
- Target Type: configurable presets plus Custom
- minimum custom target = 15 past papers
- maximum = Available Papers
- whole-number input only
- invalid target is rejected without modifying stored target
- target persists independently by student + level + subject

If Available Papers is less than 15, show the BRD-compliant unavailable/validation state rather than permitting an invalid target.

## 5. Visual palette

Use the OneView prototype palette consistently:

- Navigation dark purple: `#3514A0`
- Primary accent purple: `#5B35D5`
- Main text dark navy: `#211A4A`
- Muted text: `#6B7280`
- Canvas: `#F7F8FC`
- Cards: `#FFFFFF`
- Borders/grid: `#E8E8F1`
- Positive: `#12A66A`
- Warning/monitor: `#E49A27`
- Critical/high/needs-focus: `#D84B64`

Use restrained rounding and subtle borders/shadows. The visual intent is clean, compact, student-friendly, and aligned with the prototype—not a generic corporate BI report.

## 6. Required filters and security

Student-facing BI must be scoped to the authorized student. Dashboard context must include:

- `student_id` — fixed/hidden for authenticated student-facing embedding
- `academic_level` — visible AS/A selector

Pure Mathematics and Statistics are displayed simultaneously as independent subject panels, not chosen through a single subject filter in the primary Overview.

Optional diagnostic/admin BI may expose Year, Session, Paper, Topic, and Subtopic filters, but those must not change the student-facing Overview layout.

## 7. Semantic sources

Use Supabase as the single calculation/semantic layer. Do not reimplement formulas in Metabase/BI.

Primary sources:

- `v_bi_overview_dashboard`
- `v_overview_attempts`
- `v_overview_priority_areas`
- `v_overview_subtopic_performance`
- `v_overview_insight_recommendation`

The same student/level/subject inputs must reconcile exactly between BI, Streamlit Overview, and Topic Analysis.

## 8. Empty and insufficient-data states

Never convert analytical null/insufficient states to `0%` if that could imply actual performance.

Required copy includes:

- `Not Set` for an unset target
- `More data needed` for insufficient prediction/trend/priority/insight/recommendation states
- `0` Completed is valid when there are no attempts
- Available Papers may still display with no attempts

No weakness classification is allowed for subtopics with fewer than 3 relevant observations.

## 9. Data and rule integrity

BI is a presentation layer over the Supabase rule engine. It must preserve:

- AS and A Level isolation
- Pure Mathematics and Statistics independence
- completion against Practice Target, not Available Papers
- Prediction V1 sufficiency and weighting from the semantic layer
- exact trend result from the semantic layer
- priority classification/tie-break output from the semantic layer
- exactly one deterministic Insight and Recommendation per subject
- no duplicate attempt count after corrections

## 10. BRD visual acceptance checklist

A BI dashboard is visually acceptable only if all are true:

- left navigation matches the MVP navigation
- top header matches the BRD structure
- Pure Mathematics and Statistics are side-by-side
- both subject panels are visually symmetric
- the three KPI cards appear in the same order
- Predicted Performance appears below the KPI row
- Target Practice appears below the KPI/performance area
- Performance Trend is left of Priority Improvement Areas
- Insight and Recommendation are at the bottom of each subject panel
- Edit Target is visible and opens a popup
- no additional decorative visualization changes the hierarchy
- all prototype values are replaced by runtime data
- empty states follow BRD wording

This standard supersedes the earlier generic “Power BI-quality” styling guidance wherever that guidance differed from the BRD prototype.