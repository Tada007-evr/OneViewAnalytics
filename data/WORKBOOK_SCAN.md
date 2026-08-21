# Workbook scan and load decisions

Source workbook: `OneView_9709_Paper1_2025_Mapping-Score.xlsx`

Sheets scanned: `Taxonomy`, `2025`.

- Taxonomy rows: 36
- Taxonomy topics: 8
- Taxonomy subtopics: 36
- 2025 mapping rows: 206
- Paper instances: 9
- Question instances: 9
- Source score rows: 160
- Error Type values: 22
- Verified values: 4

## Important loading rule

The workbook contains `Score` and `Practice Date` for seven completed student practice attempts, but it does not contain a Student/Auth UUID. Therefore the metadata loader is safe to run immediately, while the scored-attempt loader is intentionally parameterized and must be run only after replacing the placeholder UUID with the intended student's Supabase Auth user ID.

`Score` is never loaded into the paper/question master tables. It belongs in `practice_attempts`, `question_results`, and `subpart_results`.
`Error Type` and `Verified` are loaded as result annotations after adding those optional columns.
