# OneView October 2026 QA & Acceptance Checklist

Use this checklist against the revised Record Practice Paper BRD v1.0.

## Authentication and access

- [ ] Student can sign in successfully.
- [ ] Unauthenticated users cannot access student practice data.
- [ ] Student A cannot view Student B practice attempts.
- [ ] Student A cannot edit Student B question/sub-part results.
- [ ] Session expiry returns the user to sign-in without exposing data.
- [ ] Production deployment uses HTTPS.

## Paper selection

- [ ] Paper is mandatory.
- [ ] Session is mandatory.
- [ ] Year is mandatory.
- [ ] Paper 1 is available with verified mapping data.
- [ ] Paper 5 is available with verified mapping data before release.
- [ ] Selecting Paper / Session / Year loads the correct database paper instance.

## Question Mapping Database

- [ ] Question structure loads dynamically from the database.
- [ ] Questions without sub-parts display correctly.
- [ ] Questions with sub-parts display correctly.
- [ ] Question Number is read-only.
- [ ] Sub-part is read-only.
- [ ] Maximum Marks is read-only.
- [ ] Topic(s) is read-only.
- [ ] Student cannot modify question/topic mappings from the practice UI.

## Marks Scored validation

- [ ] Marks Scored accepts numeric values.
- [ ] Score of 0 is accepted.
- [ ] Score equal to Maximum Marks is accepted.
- [ ] Negative score is rejected.
- [ ] Score greater than Maximum Marks is rejected.
- [ ] Non-numeric score is rejected.
- [ ] Database-level validation also prevents score > maximum marks.

## Calculations

- [ ] Question total equals sub-part total when sub-parts exist.
- [ ] Overall score equals the sum of question scores.
- [ ] Percentage uses total score / paper maximum marks * 100.
- [ ] Topic-wise score equals mapped marks scored.
- [ ] Topic-wise percentage uses mapped marks scored / mapped maximum marks.
- [ ] Approved estimated-grade rule is used after product-owner sign-off.
- [ ] No unofficial grade boundary is presented as approved.

## Notes

- [ ] Notes are optional.
- [ ] Empty notes save successfully.
- [ ] Notes up to 300 characters save successfully.
- [ ] Notes over 300 characters are prevented.
- [ ] Notes display when viewing a saved record.
- [ ] Notes can be edited.

## Save / View / Edit

- [ ] New practice paper saves successfully.
- [ ] Saved PracticeAttempt has the authenticated Student ID.
- [ ] QuestionResult rows are created correctly.
- [ ] SubpartResult rows are created correctly.
- [ ] Saved result is visible in Practice Records.
- [ ] Saved result can be viewed read-only.
- [ ] Existing result can be edited.
- [ ] Editing updates, rather than duplicates, the selected practice record.
- [ ] Updated scores recalculate total and percentage.
- [ ] Updated notes persist.

## Dashboard integration

- [ ] Overview summary cards update after save.
- [ ] Overview contains Paper 1 panel.
- [ ] Overview contains Paper 5 panel.
- [ ] Overview shows recent practice papers.
- [ ] Overall AS summary reflects saved data.
- [ ] Topic Analysis reflects saved data.
- [ ] Progress reflects saved data.
- [ ] Reports reflect saved data.

## Data integrity

- [ ] Each paper instance has the correct year/session/paper code.
- [ ] Paper maximum marks reconcile with verified source data.
- [ ] Every analytics mapping has a valid topic.
- [ ] Subtopic mapping is valid where supplied.
- [ ] Existing historical results survive new mapping/paper loads.
- [ ] No hard-coded foreign-key UUIDs are required for new mapping imports.

## Non-functional requirements

- [ ] Normal page-load target (<3 seconds) measured in production.
- [ ] Normal save target (<2 seconds) measured in production.
- [ ] Chrome smoke test passes.
- [ ] Edge smoke test passes.
- [ ] Firefox smoke test passes.
- [ ] Safari smoke test passes.
- [ ] Desktop layout passes.
- [ ] Laptop layout passes.

## Release blockers

- [ ] Verified Paper 5 mapping dataset supplied and loaded.
- [ ] Approved estimated-grade boundaries/rules supplied and implemented.
- [ ] `sql/07_record_practice_brd_v1.sql` applied to production Supabase.
- [ ] No critical/high defects remain open.
- [ ] Product owner accepts the release candidate.

## Release sign-off

- Product owner: ____________________ Date: __________
- QA: ______________________________ Date: __________
- Release version/tag: ______________
