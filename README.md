# OneView Learning Analytics — Free MVP Stack

This implementation follows the supplied BRD and uses:

- **UI / application:** Python + Streamlit
- **Database + authentication:** Supabase Postgres + Supabase Auth
- **BI:** Metabase Open Source, self-hosted
- **Analytics:** SQL views + Python/Streamlit calculations
- **Deployment:** Streamlit Community Cloud for the app; Metabase can run locally/Docker or on any free/self-managed host that supports Docker.

The BRD calls for a desktop/laptop web app, a Student ID based relational model, question/sub-part score entry, topic analytics, progress tracking, predicted performance, and rule-based insights. fileciteturn0file0L17-L31

## Important data note

The BRD does not contain the actual Cambridge past-paper/question/sub-part/topic dataset. Therefore `sql/02_demo_seed.sql` contains clearly labelled DEMO records only. Replace those records with verified Cambridge source data before using the analytics as real student guidance.

## 1. Create the free database

1. Create a free Supabase project.
2. Open **SQL Editor**.
3. Run `sql/01_schema.sql`.
4. Run `sql/02_demo_seed.sql`.
5. In Supabase Auth, enable Email/Password.
6. Create a test student account.
7. In the `students` table, add/update the matching profile row if your Auth trigger is not enabled.

Supabase's free tier currently includes a Postgres database, 500 MB database storage, and Auth; free projects can pause after inactivity. See the official pricing/docs before production use.

## 2. Configure the Streamlit app

Create `.streamlit/secrets.toml` locally:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_ANON_KEY = "YOUR_ANON_KEY"
```

Install:

```bash
pip install -r requirements.txt
streamlit run app/main.py
```

The app provides:

- Login
- Overview dashboard
- Practice paper selection
- Question/sub-part score entry
- Immediate mark validation
- Save to database
- Practice history
- Topic performance
- Rule-based insight cards

## 3. Deploy the free UI

Push this folder to GitHub.

Deploy with Streamlit Community Cloud:

1. Sign in to Streamlit Community Cloud.
2. Connect GitHub.
3. Select the repository and `app/main.py`.
4. Add the two Supabase secrets in the app's Secrets configuration.
5. Deploy.

## 4. BI with free Metabase Open Source

Use the included `metabase/docker-compose.yml`.

Run:

```bash
cd metabase
docker compose up -d
```

Then open Metabase locally at:

`http://localhost:3000`

Create a Metabase database connection to the same Supabase Postgres database.

Use the SQL views created by `sql/03_bi_views.sql` as the BI semantic layer.

## 5. Build these dashboards in Metabase

### Dashboard 1 — Student Overview
Cards:
- Papers completed
- Planned papers
- Completion %
- Average %
- Estimated performance
- Recent trend
- Strongest topics
- Weakest topics

### Dashboard 2 — Topic Weakness
Charts:
- Topic average %
- Marks lost by topic
- Attempt count by topic
- Repeated weakness count

### Dashboard 3 — Paper Progress
Charts:
- Attempts by year
- Attempts by session
- Score % by paper/date
- Completion burndown

### Dashboard 4 — Question Analysis
Charts:
- Average question %
- Marks lost by question
- Lowest-performing questions
- Question performance over time

The BRD explicitly requires overview, topic analytics, reports/progress, predicted performance, and intelligent insights. fileciteturn0file0L133-L142 fileciteturn0file0L168-L193

## 6. End-to-end test

1. Register/login.
2. Select AS Mathematics.
3. Select year/session/paper.
4. Enter question scores.
5. Enter sub-part scores where present.
6. Confirm invalid scores are rejected.
7. Submit.
8. Confirm the attempt is stored.
9. Confirm dashboard metrics update.
10. Confirm topic performance updates.
11. Open Metabase and refresh the dashboard.
12. Confirm the same stored records appear in BI.

These tests map directly to the BRD acceptance criteria. fileciteturn0file0L312-L326

## 7. What remains before a real pilot

- Load verified Cambridge paper/question/sub-part metadata.
- Finalize the controlled topic/subtopic taxonomy.
- Review all question-to-topic mappings.
- Decide the exact V1 prediction formula with the product owner.
- Configure production backup/export.
- Perform security review of Auth/RLS.
- Replace demo data.

The BRD specifically identifies question/topic data preparation and incorrect topic mapping as high risks. fileciteturn0file0L345-L363


## Dataset now included

The supplied workbook `9709_2025_Paper_1_OneView_Mapping_All_Variants.xlsx` was inspected and converted into `sql/02_real_dataset_seed.sql`.

Verified from the workbook:

- 9 2025 Paper 1 variants across February/March, May/June and October/November.
- 207 Detailed Mapping rows.
- 96 top-level questions.
- 184 marked sub-part rows.
- Every mapped paper totals 75 marks.
- 8 subject topics are used in Detailed Mapping.
- 20 top-level questions have topic changes between sub-parts, so the database maps topics at sub-part level where necessary.

Before production analytics sign-off, review `DATA_VALIDATION.md`. The workbook's Detailed Mapping and Final Taxonomy sheets contain several subtopic naming differences. The import deliberately preserves the Detailed Mapping values rather than silently changing the source data.

### Import order

Run in Supabase SQL Editor:

1. `sql/01_schema.sql`
2. `sql/02_real_dataset_seed.sql`
3. `sql/03_bi_views.sql`

Do not run the old `sql/02_demo_seed.sql` if you are using the real supplied dataset.
