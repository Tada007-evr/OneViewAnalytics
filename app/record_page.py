import pandas as pd
import streamlit as st
from oneview_db import build_grid, get_df, save_attempt, validate_grid


def render_record_practice(sb, user):
    st.markdown("<div class='ov-kicker'>RECORD PRACTICE PAPER</div>", unsafe_allow_html=True)
    st.title("Record Practice Paper")
    c1, c2 = st.columns(2)
    with c1:
        level = st.selectbox("Exam Level", ["AS Level", "A Level"], index=0 if st.session_state.get("overview_level", "AS Level") == "AS Level" else 1)
    with c2:
        subject = st.selectbox("Subject", ["Pure Mathematics", "Statistics"])

    papers = get_df(sb, "exam_papers", "*", {"academic_level": level, "subject": subject, "eligible": True})
    if papers.empty:
        st.info("No eligible papers are currently available for this level and subject.")
        return

    papers = papers.copy()
    papers["Paper"] = papers["paper_code"].map(lambda code: "Paper 1" if str(code).split("/")[1].startswith("1") else "Paper 5")
    a, b, c = st.columns(3)
    with a:
        paper_type = st.selectbox("Paper", sorted(papers["Paper"].unique().tolist()))
    subset = papers[papers["Paper"] == paper_type]
    with b:
        session = st.selectbox("Session", sorted(subset["session"].unique().tolist()))
    subset = subset[subset["session"] == session]
    with c:
        year = st.selectbox("Year", sorted(subset["year"].astype(int).unique().tolist(), reverse=True))
    subset = subset[subset["year"].astype(int) == int(year)]
    labels = subset.apply(lambda row: f"{row['paper_code']} · {float(row['total_marks']):g} marks", axis=1).tolist()
    selected = st.selectbox("Paper Variant", labels)
    paper = subset.iloc[labels.index(selected)]

    existing = get_df(sb, "practice_attempts", "attempt_id,notes", {
        "student_id": user.id, "paper_id": paper["paper_id"], "status": "completed"
    }, order="updated_at", desc=True)
    attempt_id = existing.iloc[0]["attempt_id"] if not existing.empty else None
    notes_value = (existing.iloc[0].get("notes") or "") if not existing.empty else ""
    if attempt_id:
        st.info("A saved attempt exists for this paper. Saving will correct that record rather than create a duplicate attempt.")

    grid = build_grid(sb, paper["paper_id"], attempt_id)
    if grid.empty:
        st.warning("No question mapping is available for this paper.")
        return

    edited = st.data_editor(
        grid[["Question", "Sub-part", "Maximum Marks", "Topic / Subtopic", "Marks Scored"]],
        hide_index=True,
        use_container_width=True,
        disabled=["Question", "Sub-part", "Maximum Marks", "Topic / Subtopic"],
        column_config={
            "Maximum Marks": st.column_config.NumberColumn(format="%.0f"),
            "Marks Scored": st.column_config.NumberColumn(min_value=0.0, step=1.0),
            "Topic / Subtopic": st.column_config.TextColumn(width="large"),
        },
        key=f"grid_{paper['paper_id']}_{attempt_id or 'new'}",
    )
    work = grid.copy()
    work["Marks Scored"] = edited["Marks Scored"].values
    errors = validate_grid(work)
    total = float(pd.to_numeric(work["Marks Scored"], errors="coerce").fillna(0).sum())
    percentage = total / float(paper["total_marks"]) * 100
    x1, x2 = st.columns(2)
    x1.metric("Total Marks", f"{total:g} / {float(paper['total_marks']):g}")
    x2.metric("Percentage", f"{percentage:.1f}%")
    notes = st.text_area("Notes (optional)", value=notes_value, max_chars=300)
    for error in errors:
        st.error(error)

    label = "Update Practice Paper" if attempt_id else "Save Practice Paper"
    if st.button(label, type="primary", disabled=bool(errors), use_container_width=True):
        try:
            total, percentage, _ = save_attempt(sb, user, paper, work, notes, attempt_id)
            st.success(f"Practice paper saved: {total:g}/{float(paper['total_marks']):g} ({percentage:.1f}%). Overview analytics have been recalculated.")
            st.session_state.nav = "Overview"
            st.rerun()
        except Exception as exc:
            st.error(f"Save failed: {exc}")
