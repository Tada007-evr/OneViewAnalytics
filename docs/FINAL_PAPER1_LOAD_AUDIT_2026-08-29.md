# Final Paper 1 workbook load audit — 2026-08-29

Source: `FINAL_OneView_9709_Paper1_Mapping_Score.xlsx` supplied for the OneView Practice Paper flow.

## Workbook checks before load

- Taxonomy rows: 36
- Topics: 8
- Paper/detail rows: 206
- Distinct 2025 paper variants: 9
- Distinct parent questions: 96
- Sub-part rows: 183
- Whole-question rows: 23
- Duplicate leaf question/sub-part rows: 0
- Topic/Sub-topic values not present in Taxonomy: 0
- Papers whose leaf Max Marks did not sum to 75: 0
- Scores below 0 or above Max Marks: 0

## Loaded production counts

- `topics`: 8
- `subtopics`: 36
- `exam_papers`: 9
- `questions`: 96
- `sub_parts`: 183
- `question_topics`: 23
- `subpart_topics`: 183
- `practice_attempts`: 9
- `question_results`: 96
- `subpart_results`: 183

A full source-to-database leaf reconciliation covering paper/session/question/sub-part, Max Marks, Score, Topic, Sub-topic, raw error type, normalized error type and Verified returned **0 mismatches**.

## Loaded paper totals

| Session | Paper | Practice date | Score | Percentage |
|---|---|---:|---:|---:|
| February/March | 9709/12 | 2026-08-07 | 73/75 | 97.33% |
| May/June | 9709/11 | 2026-08-20 | 72/75 | 96.00% |
| May/June | 9709/12 | 2026-08-21 | 72/75 | 96.00% |
| May/June | 9709/13 | 2026-08-11 | 70/75 | 93.33% |
| May/June | 9709/15 | 2026-08-13 | 70/75 | 93.33% |
| October/November | 9709/11 | 2026-08-17 | 69/75 | 92.00% |
| October/November | 9709/12 | 2026-08-18 | 70/75 | 93.33% |
| October/November | 9709/13 | 2026-08-18 | 72/75 | 96.00% |
| October/November | 9709/15 | 2026-08-19 | 71/75 | 94.67% |

## Error Type handling

The workbook contains legacy Error Type labels that do not exactly match the finalized Record Practice Paper BRD controlled list. The raw workbook text is preserved in `source_error_type`; normalized `error_type` is used by the current app.

| Workbook label | BRD normalized value |
|---|---|
| Incorrect formula | Forgot Formula / Rule |
| Calclation error | Calculation Error |
| Careless | Careless Error |
| Missed step | Incomplete Answer |
| Knowledge gap | Conceptual Error |
| Simplification | Calculation Error |
| Approximation | Calculation Error |
| Content clarity | Conceptual Error |
| Graph | Application Error |

One workbook row has Marks Lost > 0 with a blank Error Type: October/November 2025, paper 9709/15, Q11(c)(ii). The load intentionally preserves that absence rather than inventing a category. When that saved attempt is edited in the Practice Paper UI, the BRD validation requires the student to select a controlled Error Type before the update can be saved.

## Post-load checks

- Null Topic/Sub-topic mappings: 0
- Invalid question scores: 0
- Invalid sub-part scores: 0
- Duplicate completed Student + Paper attempts: 0
- Error types outside the BRD controlled list: 0
- `v_attempt_history` rows: 9
- `v_topic_performance` rows: 8
- `v_bi_overview_dashboard` rows: 4
- AS Level Pure Mathematics papers completed in Overview: 9

The temporary import staging tables are removed after validation.
