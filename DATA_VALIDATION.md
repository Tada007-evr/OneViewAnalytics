# Dataset validation report

Source: `9709_2025_Paper_1_OneView_Mapping_All_Variants.xlsx`

## Confirmed dataset structure

- 9 papers across 3 sessions.
- Paper codes: 9709/11, 9709/12, 9709/13 and 9709/15.
- 207 Detailed Mapping rows.
- 96 top-level questions.
- 23 questions without sub-parts.
- 184 marked sub-part rows.
- Every paper totals 75 marks from the supplied mapping.
- 8 topics appear in Detailed Mapping.
- The Final Taxonomy contains 37 rows.

## Taxonomy discrepancy — requires a decision

Detailed Mapping subtopic labels not found in Final Taxonomy:
- Area of a sector
- Straight line equations
- Transformation of functions

Final Taxonomy labels not found in Detailed Mapping:
- Chain rule
- Improper integrals
- Integration of expressions
- Inverse trigonometric functions
- Length of line segment and midpoint
- Quadratic curves
- Straight-line equations
- Transformations of functions

The database import preserves the Detailed Mapping assignments exactly rather than silently renaming or merging categories.

## Important database design finding

20 top-level questions have different topics across their marked sub-parts. Therefore topic/subtopic mapping is implemented at both question and sub-part level. This is necessary for accurate analytics and follows the BRD requirement that question/sub-part mappings support analytics.
