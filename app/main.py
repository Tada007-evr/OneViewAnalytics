import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="OneView Learning Analytics", page_icon="📘", layout="wide")

SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY"))
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("Configure SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets.")
    st.stop()

sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def query(table, select="*"):
    return sb.table(table).select(select)


def get_df(table, select="*", filters=None):
    q = query(table, select)
    for col, val in (filters or {}).items():
        q = q.eq(col, val)
    return pd.DataFrame(q.execute().data or [])


def paper_type(code):
    try:
        family = str(code).split("/", 1)[1][0]
        return {"1": "Paper 1", "5": "Paper 5"}.get(family)
    except Exception:
        return None


def estimate_grade(_percentage):
    # The BRD requires an estimated grade but supplies no approved boundaries.
    return "Pending approved grade boundaries"


def login():
    st.title("📘 OneView Learning Analytics")
    st.caption("Cambridge AS Level Mathematics — Record Practice Paper")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    if st.button("Sign in", type="primary", use_container_width=True):
        try:
            res = sb.auth.sign_in_with_password({"email": email, "password": password})
            if res.user and res.session:
                st.session_state.user = res.user
                st.session_state.access_token = res.session.access_token
                st.session_state.refresh_token = res.session.refresh_token
                st.rerun()
            st.error("No authenticated session was returned.")
        except Exception as exc:
            st.error(f"Sign-in failed: {exc}")


def current_student():
    access = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")
    if not access or not refresh:
        return None
    try:
        res = sb.auth.set_session(access, refresh)
        if res and res.user:
            st.session_state.user = res.user
            if res.session:
                st.session_state.access_token = res.session.access_token
                st.session_state.refresh_token = res.session.refresh_token
            return res.user
    except Exception:
        for key in ("user", "access_token", "refresh_token"):
            st.session_state.pop(key, None)
    return None


def mapping_labels():
    topics = get_df("topics", "topic_id,topic_name")
    subtopics = get_df("subtopics", "subtopic_id,subtopic_name")
    qmap = get_df("question_topics", "question_id,topic_id,subtopic_id")
    smap = get_df("subpart_topics", "sub_part_id,topic_id,subtopic_id")
    tn = dict(zip(topics.get("topic_id", []), topics.get("topic_name", [])))
    sn = dict(zip(subtopics.get("subtopic_id", []), subtopics.get("subtopic_name", [])))

    def build(frame, id_col):
        result = {}
        if frame.empty:
            return result
        for rid, grp in frame.groupby(id_col):
            labels = []
            for _, row in grp.iterrows():
                t = tn.get(row.get("topic_id"), "")
                s = sn.get(row.get("subtopic_id"), "")
                label = f"{t} — {s}" if t and s else (t or s)
                if label and label not in labels:
                    labels.append(label)
            result[rid] = "; ".join(labels)
        return result

    return build(qmap, "question_id"), build(smap, "sub_part_id")


def build_grid(paper_id, attempt_id=None):
    qs = get_df("questions", "question_id,paper_id,question_number,max_marks", {"paper_id": paper_id})
    if qs.empty:
        return pd.DataFrame()
    sp = get_df("sub_parts", "sub_part_id,question_id,label,max_marks")
    sp = sp[sp["question_id"].isin(qs["question_id"].tolist())] if not sp.empty else sp
    qtopics, sptopics = mapping_labels()

    qr_lookup, sr_lookup = {}, {}
    if attempt_id:
        qr = get_df("question_results", "question_result_id,question_id,score", {"attempt_id": attempt_id})
        if not qr.empty:
            qr_lookup = {r["question_id"]: r for _, r in qr.iterrows()}
            ids = qr["question_result_id"].tolist()
            sr = get_df("subpart_results", "question_result_id,sub_part_id,score")
            if not sr.empty:
                sr = sr[sr["question_result_id"].isin(ids)]
                sr_lookup = {r["sub_part_id"]: float(r["score"]) for _, r in sr.iterrows()}

    rows = []
    qs = qs.copy()
    qs["_n"] = pd.to_numeric(qs["question_number"], errors="coerce")
    for _, q in qs.sort_values(["_n", "question_number"]).iterrows():
        parts = sp[sp["question_id"] == q["question_id"]] if not sp.empty else pd.DataFrame()
        if not parts.empty:
            for _, p in parts.sort_values("label").iterrows():
                rows.append({
                    "question_id": q["question_id"],
                    "sub_part_id": p["sub_part_id"],
                    "Question": str(q["question_number"]),
                    "Sub-part": str(p["label"]),
                    "Maximum Marks": float(p["max_marks"]),
                    "Topic(s)": sptopics.get(p["sub_part_id"], qtopics.get(q["question_id"], "")),
                    "Marks Scored": sr_lookup.get(p["sub_part_id"], 0.0),
                })
        else:
            prev = qr_lookup.get(q["question_id"], {})
            rows.append({
                "question_id": q["question_id"],
                "sub_part_id": None,
                "Question": str(q["question_number"]),
                "Sub-part": "",
                "Maximum Marks": float(q["max_marks"]),
                "Topic(s)": qtopics.get(q["question_id"], ""),
                "Marks Scored": float(prev.get("score", 0) or 0),
            })
    return pd.DataFrame(rows)


def validate_grid(grid):
    errors = []
    for _, row in grid.iterrows():
        try:
            score = float(row["Marks Scored"] or 0)
        except Exception:
            errors.append(f"Question {row['Question']}: Marks Scored must be numeric.")
            continue
        maximum = float(row["Maximum Marks"])
        if score < 0 or score > maximum:
            suffix = f" {row['Sub-part']}" if row["Sub-part"] else ""
            errors.append(f"Question {row['Question']}{suffix}: score must be between 0 and {maximum:g}.")
    return errors


def topic_summary(grid):
    work = grid.copy()
    work["Topic"] = work["Topic(s)"].fillna("").map(
        lambda x: str(x).split(" — ", 1)[0].split(";", 1)[0].strip() or "Unmapped"
    )
    out = work.groupby("Topic", as_index=False).agg(
        Marks_Scored=("Marks Scored", "sum"),
        Maximum_Marks=("Maximum Marks", "sum"),
    )
    out["Percentage"] = out.apply(
        lambda r: r["Marks_Scored"] / r["Maximum_Marks"] * 100 if r["Maximum_Marks"] else 0,
        axis=1,
    )
    return out.sort_values("Percentage")


def save_attempt(user, paper, grid, notes, attempt_id=None):
    total = float(pd.to_numeric(grid["Marks Scored"], errors="coerce").fillna(0).sum())
    maximum = float(paper["total_marks"])
    pct = total / maximum * 100 if maximum else 0
    payload = {
        "student_id": user.id,
        "paper_id": paper["paper_id"],
        "attempt_date": str(date.today()),
        "status": "completed",
        "total_score": total,
        "percentage": round(pct, 2),
        "notes": notes.strip() or None,
        "estimated_grade": estimate_grade(pct),
    }

    if attempt_id:
        sb.table("practice_attempts").update(payload).eq("attempt_id", attempt_id).execute()
    else:
        attempt_id = sb.table("practice_attempts").insert(payload).execute().data[0]["attempt_id"]

    qr = get_df("question_results", "question_result_id,question_id", {"attempt_id": attempt_id})
    qr_lookup = dict(zip(qr["question_id"], qr["question_result_id"])) if not qr.empty else {}

    for qid, rows in grid.groupby("question_id"):
        qscore = float(pd.to_numeric(rows["Marks Scored"], errors="coerce").fillna(0).sum())
        qr_id = qr_lookup.get(qid)
        if qr_id:
            sb.table("question_results").update({"score": qscore}).eq("question_result_id", qr_id).execute()
        else:
            qr_id = sb.table("question_results").insert(
                {"attempt_id": attempt_id, "question_id": qid, "score": qscore}
            ).execute().data[0]["question_result_id"]

        if rows["sub_part_id"].notna().any():
            sr = get_df("subpart_results", "subpart_result_id,sub_part_id", {"question_result_id": qr_id})
            sr_lookup = dict(zip(sr["sub_part_id"], sr["subpart_result_id"])) if not sr.empty else {}
            for _, row in rows.iterrows():
                spid = row["sub_part_id"]
                if not spid:
                    continue
                score = float(row["Marks Scored"] or 0)
                if spid in sr_lookup:
                    sb.table("subpart_results").update({"score": score}).eq(
                        "subpart_result_id", sr_lookup[spid]
                    ).execute()
                else:
                    sb.table("subpart_results").insert(
                        {"question_result_id": qr_id, "sub_part_id": spid, "score": score}
                    ).execute()
    return total, pct


def select_paper():
    papers = get_df("exam_papers", "paper_id,academic_level,subject,year,session,paper_code,total_marks")
    if papers.empty:
        st.warning("No papers are available in the Question Mapping Database.")
        return None
    papers = papers.copy()
    papers["Paper"] = papers["paper_code"].map(paper_type)
    papers = papers[papers["Paper"].isin(["Paper 1", "Paper 5"])]
    if papers.empty:
        st.warning("No Paper 1 or Paper 5 records are available.")
        return None

    c1, c2, c3 = st.columns(3)
    with c1:
        ptype = st.selectbox("Paper *", [x for x in ("Paper 1", "Paper 5") if x in papers["Paper"].unique()])
    subset = papers[papers["Paper"] == ptype]
    with c2:
        session = st.selectbox("Session *", sorted(subset["session"].unique().tolist()))
    subset = subset[subset["session"] == session]
    with c3:
        year = st.selectbox("Year *", sorted(subset["year"].astype(int).unique().tolist(), reverse=True))
    subset = subset[subset["year"].astype(int) == int(year)]
    if len(subset) > 1:
        labels = subset.apply(lambda r: f"{r['paper_code']} ({float(r['total_marks']):g} marks)", axis=1).tolist()
        label = st.selectbox("Paper variant", labels)
        return subset.iloc[labels.index(label)]
    return subset.iloc[0]


def practice_form(user, paper, attempt_id=None, notes_value="", mode="new"):
    grid = build_grid(paper["paper_id"], attempt_id)
    if grid.empty:
        st.warning("No question mapping is available for this paper.")
        return

    st.info(
        f"{paper_type(paper['paper_code'])} · {paper['paper_code']} · "
        f"{paper['session']} {int(paper['year'])} · Maximum {float(paper['total_marks']):g}"
    )
    source = grid[["Question", "Sub-part", "Maximum Marks", "Topic(s)", "Marks Scored"]].copy()
    edited = st.data_editor(
        source,
        hide_index=True,
        use_container_width=True,
        disabled=["Question", "Sub-part", "Maximum Marks", "Topic(s)"],
        column_config={
            "Question": st.column_config.TextColumn("Question Number"),
            "Sub-part": st.column_config.TextColumn("Sub-part"),
            "Maximum Marks": st.column_config.NumberColumn("Maximum Marks", format="%.0f"),
            "Topic(s)": st.column_config.TextColumn("Topic(s)", width="large"),
            "Marks Scored": st.column_config.NumberColumn("Marks Scored", min_value=0.0, step=1.0),
        },
        key=f"practice_{attempt_id or paper['paper_id']}",
    )
    work = grid.copy()
    work["Marks Scored"] = edited["Marks Scored"].values
    errors = validate_grid(work)

    total = float(pd.to_numeric(work["Marks Scored"], errors="coerce").fillna(0).sum())
    maximum = float(paper["total_marks"])
    pct = total / maximum * 100 if maximum else 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Marks", f"{total:g}/{maximum:g}")
    c2.metric("Percentage", f"{pct:.1f}%")
    c3.metric("Estimated Grade", estimate_grade(pct))
    st.caption("Approved grade boundaries were not supplied in the BRD, so OneView does not invent them.")

    st.subheader("Topic-wise performance")
    summary = topic_summary(work)
    display = summary.copy()
    display["Marks"] = display.apply(lambda r: f"{r['Marks_Scored']:g}/{r['Maximum_Marks']:g}", axis=1)
    display["Percentage"] = display["Percentage"].map(lambda v: f"{v:.1f}%")
    st.dataframe(display[["Topic", "Marks", "Percentage"]], hide_index=True, use_container_width=True)

    notes = st.text_area("Notes (optional)", value=notes_value or "", max_chars=300)
    st.caption(f"{len(notes)}/300 characters")
    for error in errors:
        st.error(error)

    label = "Update Practice Record" if mode == "edit" else "Save Practice Paper"
    if st.button(label, type="primary", disabled=bool(errors), use_container_width=True):
        try:
            saved_total, saved_pct = save_attempt(user, paper, work, notes, attempt_id)
            st.success(
                f"Practice paper {'updated' if mode == 'edit' else 'saved'} successfully: "
                f"{saved_total:g}/{maximum:g} ({saved_pct:.1f}%). Analytics update from this saved record."
            )
            st.rerun()
        except Exception as exc:
            if "notes" in str(exc) or "estimated_grade" in str(exc):
                st.error("Run sql/07_record_practice_brd_v1.sql in Supabase, then retry.")
            else:
                st.error(f"Save failed: {exc}")


def record_practice(user):
    st.title("Record Practice Paper")
    st.caption(
        "Question Number, Sub-part, Maximum Marks and Topic(s) are read-only from the Question Mapping Database. "
        "Marks Scored is the only editable question field."
    )
    paper = select_paper()
    if paper is not None:
        practice_form(user, paper)


def practice_history(user):
    try:
        attempts = get_df(
            "practice_attempts",
            "attempt_id,student_id,paper_id,attempt_date,total_score,percentage,status,notes,estimated_grade",
            {"student_id": user.id},
        )
    except Exception as exc:
        if "notes" in str(exc) or "estimated_grade" in str(exc):
            st.error("Run sql/07_record_practice_brd_v1.sql in Supabase to enable revised BRD record fields.")
            return
        raise
    papers = get_df("exam_papers", "paper_id,year,session,paper_code,total_marks")
    if attempts.empty:
        st.info("No practice records yet.")
        return
    history = attempts.merge(papers, on="paper_id", how="left").sort_values("attempt_date", ascending=False)
    view = history[["attempt_date", "paper_code", "session", "year", "total_score", "total_marks", "percentage", "estimated_grade"]].copy()
    view.columns = ["Date", "Paper", "Session", "Year", "Score", "Max", "Percentage", "Estimated Grade"]
    view["Percentage"] = view["Percentage"].map(lambda v: f"{float(v):.1f}%")
    st.dataframe(view, hide_index=True, use_container_width=True)

    labels = history.apply(
        lambda r: f"{r['attempt_date']} · {r['paper_code']} · {r['session']} {int(r['year'])} · {float(r['percentage']):.1f}%",
        axis=1,
    ).tolist()
    selected = st.selectbox("Select a saved record", labels)
    row = history.iloc[labels.index(selected)]
    view_tab, edit_tab = st.tabs(["View", "Edit"])
    with view_tab:
        c1, c2, c3 = st.columns(3)
        c1.metric("Score", f"{float(row['total_score']):g}/{float(row['total_marks']):g}")
        c2.metric("Percentage", f"{float(row['percentage']):.1f}%")
        c3.metric("Estimated Grade", row.get("estimated_grade") or "—")
        st.write("**Notes:**", row.get("notes") or "—")
        detail = build_grid(row["paper_id"], row["attempt_id"])
        if not detail.empty:
            detail["Marks"] = detail.apply(
                lambda r: f"{float(r['Marks Scored']):g}/{float(r['Maximum Marks']):g}", axis=1
            )
            st.dataframe(detail[["Question", "Sub-part", "Topic(s)", "Marks"]], hide_index=True, use_container_width=True)
    with edit_tab:
        practice_form(user, row, row["attempt_id"], row.get("notes") or "", mode="edit")


def dashboard(user):
    st.title("Overview")
    attempts = get_df(
        "practice_attempts",
        "attempt_id,student_id,paper_id,attempt_date,total_score,percentage,status",
        {"student_id": user.id},
    )
    papers = get_df("exam_papers", "paper_id,year,session,paper_code,total_marks")
    papers = papers.copy()
    if not papers.empty:
        papers["Paper"] = papers["paper_code"].map(paper_type)
        papers = papers[papers["Paper"].isin(["Paper 1", "Paper 5"])]
    merged = attempts.merge(papers, on="paper_id", how="left") if not attempts.empty and not papers.empty else pd.DataFrame()

    completed = len(merged)
    avg = float(merged["percentage"].mean()) if completed else 0
    latest = float(merged.sort_values("attempt_date").iloc[-1]["percentage"]) if completed else 0
    best = float(merged["percentage"].max()) if completed else 0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Papers Practised", completed)
    c2.metric("Average", f"{avg:.1f}%")
    c3.metric("Latest", f"{latest:.1f}%")
    c4.metric("Best", f"{best:.1f}%")

    st.subheader("AS Level Summary")
    left, right = st.columns(2)
    for col, label in ((left, "Paper 1"), (right, "Paper 5")):
        with col:
            subset = merged[merged["Paper"] == label] if not merged.empty else pd.DataFrame()
            available = papers[papers["Paper"] == label] if not papers.empty else pd.DataFrame()
            pav = float(subset["percentage"].mean()) if not subset.empty else 0
            st.markdown(f"### {label}")
            st.metric("Average", f"{pav:.1f}%")
            st.caption(f"{len(subset)} practice record(s) · {len(available)} mapped variant(s)")
            if available.empty:
                st.info(f"No {label} mapping data is currently loaded.")

    st.subheader("Recent Practice Papers")
    if merged.empty:
        st.info("No practice records yet.")
    else:
        recent = merged.sort_values("attempt_date", ascending=False).head(5).copy()
        recent["percentage"] = recent["percentage"].map(lambda v: f"{float(v):.1f}%")
        st.dataframe(recent[["attempt_date", "paper_code", "session", "year", "total_score", "percentage"]], hide_index=True, use_container_width=True)


def topic_analysis(user):
    st.title("Topic Analysis")
    df = get_df("v_topic_performance", filters={"student_id": user.id})
    if df.empty:
        st.info("Topic analysis will appear after practice records are saved.")
        return
    df = df.sort_values("average_percentage")
    st.plotly_chart(
        px.bar(df, x="average_percentage", y="topic_name", orientation="h",
               labels={"average_percentage": "Average %", "topic_name": "Topic"}),
        use_container_width=True,
    )
    st.dataframe(df, hide_index=True, use_container_width=True)


def progress(user):
    st.title("Progress")
    df = get_df("v_attempt_history", filters={"student_id": user.id})
    if df.empty:
        st.info("Progress will appear after practice records are saved.")
        return
    df = df.sort_values("attempt_date")
    df["Paper"] = df["paper_code"].map(paper_type)
    st.plotly_chart(
        px.line(df, x="attempt_date", y="percentage", color="Paper", markers=True,
                hover_data=["paper_code", "session", "year"]),
        use_container_width=True,
    )


def reports(user):
    st.title("Reports")
    attempts = get_df("v_attempt_history", filters={"student_id": user.id})
    topics = get_df("v_topic_performance", filters={"student_id": user.id})
    if attempts.empty:
        st.info("Reports will appear after practice records are saved.")
        return
    st.subheader("Practice History")
    st.dataframe(attempts.sort_values("attempt_date", ascending=False), hide_index=True, use_container_width=True)
    st.download_button("Download practice history CSV", attempts.to_csv(index=False).encode("utf-8"),
                       "oneview_practice_history.csv", "text/csv")
    if not topics.empty:
        st.subheader("Topic Performance")
        st.dataframe(topics.sort_values("average_percentage"), hide_index=True, use_container_width=True)
        st.download_button("Download topic analysis CSV", topics.to_csv(index=False).encode("utf-8"),
                           "oneview_topic_analysis.csv", "text/csv")


def app():
    user = current_student()
    if not user:
        login()
        return
    with st.sidebar:
        st.markdown("## 📘 OneView")
        st.caption(user.email or "Signed in")
        page = st.radio("Navigation", [
            "Overview", "Record Practice Paper", "Practice Records",
            "Topic Analysis", "Progress", "Reports"
        ])
        if st.button("Sign out", use_container_width=True):
            try:
                sb.auth.sign_out()
            except Exception:
                pass
            for key in ("user", "access_token", "refresh_token"):
                st.session_state.pop(key, None)
            st.rerun()

    if page == "Overview":
        dashboard(user)
    elif page == "Record Practice Paper":
        record_practice(user)
    elif page == "Practice Records":
        practice_history(user)
    elif page == "Topic Analysis":
        topic_analysis(user)
    elif page == "Progress":
        progress(user)
    else:
        reports(user)


app()
