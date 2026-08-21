# Loading the supplied workbook into OneView

Source: `OneView_9709_Paper1_2025_Mapping-Score.xlsx`

The workbook has two tabs and both were scanned:
- `Taxonomy`: 36 taxonomy rows, 8 topics, 36 subtopics.
- `2025`: 206 mapping rows covering 9 paper instances, all 75 marks.

## Run order in Supabase SQL Editor

1. Existing project schema: `sql/01_schema.sql` (only if tables do not already exist).
2. `sql/04_load_workbook_metadata.sql`
3. `sql/05_add_result_annotations.sql`
4. `sql/03_bi_views.sql`
5. `sql/06_optional_load_existing_scores.sql` **only after replacing the placeholder student UUID**.

## What is loaded

The metadata loader loads the exact source taxonomy, paper instances, questions, sub-parts, question-level mappings and sub-part-level mappings. It preserves the workbook terminology; it does not silently reconcile taxonomy labels.

The workbook also contains 160 non-blank `Score` cells grouped into seven completed practice attempts. Those scores are intentionally NOT loaded by the metadata script because the workbook does not contain a Student/Auth UUID. `06_optional_load_existing_scores.sql` loads those scores into `practice_attempts`, `question_results`, and `subpart_results` after you replace the placeholder UUID.

The workbook also has 22 `Error Type` values and 4 `Verified` values. `05_add_result_annotations.sql` adds those optional fields to the result tables and the score loader preserves them.

## Validation

After loading, each of the 9 paper instances should total 75 marks.
See `data/paper_validation.csv` and `data/WORKBOOK_SCAN.md`.
