# OneView Learning Analytics — October 2026 Release Plan

## Release scope

This release plan is grounded in the revised **Record Practice Paper BRD v1.0** supplied for OneView Learning Analytics.

In scope for the October 2026 release:

- Cambridge AS Level Mathematics (9709)
- Paper 1 — Pure Mathematics 1
- Paper 5 — Probability & Statistics 1
- Student login integration
- Record Practice Paper
- Question-level marks entry, including questions with and without sub-parts
- Dynamic question structure from the Question Mapping Database
- Read-only Question Number, Sub-part, Maximum Marks and Topic(s)
- Marks Scored as the editable question field
- Automatic totals, percentage, estimated grade and topic-wise performance
- Optional notes up to 300 characters
- Save, edit and view previous records
- Overview, Topic Analysis, Progress and Reports updated from saved records
- Desktop/laptop use
- Authenticated HTTPS deployment

Out of scope for this release, per BRD:

- A Level Mathematics
- Mechanics (Paper 4)
- Parent/teacher portals
- Mobile app
- OCR
- AI recommendations

## Current implementation status

### Implemented

- Supabase authentication and student-linked records
- PostgreSQL question-mapping and practice-result schema
- Paper 1 2025 mapping dataset
- Record Practice Paper UI
- Dynamic question/sub-part loading
- Read-only mapping fields
- Marks Scored entry and range validation
- Automatic total and percentage calculation
- Topic-wise performance preview
- Optional notes field
- Save, view and edit practice records
- Overview summary
- Topic Analysis
- Progress
- Reports and CSV exports
- RLS-aware BI views
- CI syntax/dependency validation

### Release blockers requiring source data / product decision

1. **Paper 5 mapping data is not present in the repository.**
   - Required before Paper 5 can be used.
   - Do not fabricate mappings.

2. **Approved estimated-grade boundaries are not supplied in the BRD or repository.**
   - Current UI deliberately displays `Pending approved grade boundaries`.
   - Product owner must supply the approved rule/table before release.

3. **Supabase migration `sql/07_record_practice_brd_v1.sql` must be executed in the deployed Supabase project.**
   - Adds notes, estimated grade, update permissions and validation required by the revised BRD.

## Delivery timeline

### 22–31 August 2026 — Functional completion

- Apply revised Record Practice Paper UI and schema migration.
- Confirm Paper 1 save/view/edit workflow end-to-end.
- Validate question and sub-part score calculations.
- Confirm Topic Analysis, Progress and Reports update after each save.
- Obtain Paper 5 source mapping dataset.
- Obtain approved estimated-grade rule/boundaries.

Exit criteria:

- Paper 1 acceptance criteria pass.
- No database foreign-key/load errors.
- No public access to another student's records.

### 1–13 September 2026 — Paper 5 integration

- Validate supplied Paper 5 workbook/source data.
- Load Paper 5 papers/questions/sub-parts/topics into Question Mapping Database.
- Validate paper totals and topic mappings.
- Confirm Record Practice Paper dynamically supports Paper 5 without code-specific question logic.
- Add Paper 5 dashboard coverage.

Exit criteria:

- Paper 1 and Paper 5 selectable by Paper / Session / Year.
- Question Mapping Database remains the source of truth.
- All mapping fields remain read-only to students.

### 14–27 September 2026 — QA, security and performance

- Execute acceptance test checklist.
- Cross-browser QA: Chrome, Edge, Firefox and Safari.
- Test desktop/laptop target resolutions.
- Measure normal page loads against the BRD target of <3 seconds.
- Measure saves against the BRD target of <2 seconds.
- Validate HTTPS deployment.
- Validate Supabase RLS with at least two student accounts.
- Test invalid marks, empty mappings, session expiry and network errors.

Exit criteria:

- No critical/high defects.
- Student A cannot read or modify Student B data.
- Calculations independently reconciled with database values.

### 28 September–11 October 2026 — UAT and release candidate

- Product-owner review against definitive prototype.
- Student usability walkthrough.
- Validate Paper 1 and Paper 5 sample attempts.
- Confirm estimated grade uses approved product-owner rules.
- Freeze mapping taxonomy for release candidate.
- Prepare production backup/export procedure.

Exit criteria:

- Product owner signs off functional scope.
- UAT acceptance criteria pass.
- Release candidate tagged/identified.

### 12–18 October 2026 — Production readiness

- Final regression test.
- Verify Streamlit secrets and Supabase production configuration.
- Verify database backup/export.
- Verify error logging and deployment recovery steps.
- Final data-quality review.

### Target release window — October 2026

Release only after all release blockers are resolved and the acceptance checklist is green.

## Release acceptance criteria

The release is ready when:

- Student can authenticate successfully.
- Student can select Paper, Session and Year.
- Question numbers, maximum marks and topic mappings load automatically.
- Student edits only Marks Scored (plus optional Notes outside the mapping table).
- Marks are numeric, >=0 and <= maximum marks.
- Notes cannot exceed 300 characters.
- Total, percentage, topic performance and approved estimated grade calculate correctly.
- Student can save a paper.
- Student can view a saved record.
- Student can edit a saved record.
- Overview updates from saved data.
- Topic Analysis updates from saved data.
- Progress updates from saved data.
- Reports update from saved data.
- Paper 1 and Paper 5 are both populated with verified mappings.
- HTTPS/authenticated access is active.
- Supported browsers pass smoke testing.
- Performance targets have been measured and accepted.

## Release decision rule

Do not release with fabricated Paper 5 mappings or unapproved grade boundaries. Those items are requirements inputs, not implementation assumptions.
