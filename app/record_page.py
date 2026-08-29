from datetime import date

import pandas as pd
import streamlit as st

from oneview_db import ERROR_TYPES, build_grid, get_df, save_attempt, student_name, validate_grid

PAPER_TYPES = {
    "AS": {
        "Paper 1 - Pure Mathematics 1": "1",
        "Paper 5 - Probability & Statistics 1": "5",
    },
    "A": {
        "Paper 3 - Pure Mathematics 2": "3",
        "Paper 5 - Probability & Statistics 2": "5",
    },
}
ERROR_CHOICES = ERROR_TYPES[1:]
TOTAL_MARKS_MVP = 75


def _clear(keys):
    for key in keys:
        st.session_state.pop(key, None)


def _reset_record_entry():
    for key in list(st.session_state.keys()):
        if str(key).startswith("rp_"):
            st.session_state.pop(key, None)


def _paper_family(code):
    text = str(code)
    return text.split("/", 1)[1][0] if "/" in text and len(text.split("/", 1)[1]) else ""


def _variant(code):
    text = str(code)
    return text.split("/", 1)[1] if "/" in text else text


def _session_label(row):
    return f"{row['session']} {int(row['year'])}"


def _last_updated(sb, user):
    rows = get_df(
        sb,
        "practice_attempts",
        "updated_at,created_at",
        {"student_id": user.id},
        order="updated_at",
        desc=True,
    )
    if rows.empty:
        return "No activity yet"
    stamp = pd.to_datetime(rows.iloc[0].get("updated_at") or rows.iloc[0].get("created_at"), utc=True, errors="coerce")
    if pd.isna(stamp):
        return "No activity yet"
    return stamp.strftime("%d %b %Y, %I:%M %p")


def _practice_styles():
    st.markdown(
        """
        <style>
        .rp-title{font-size:1.55rem;font-weight:900;color:#211A4A;margin:.15rem 0 0}
        .rp-subtitle{font-size:.79rem;color:#7B7D90;margin:.15rem 0 1rem}
        .rp-header-name{font-size:.9rem;font-weight:850;color:#211A4A;padding-top:.45rem}
        .rp-last{font-size:.72rem;color:#777A91;text-align:right;padding:.25rem 0 .35rem}
        .rp-section{background:#fff;border:1px solid #E5E6EF;border-radius:10px;padding:14px 16px;margin:.55rem 0 .9rem}
        .rp-section-title{font-size:.82rem;font-weight:900;color:#5B35D5;letter-spacing:.01em;margin-bottom:.15rem}
        .rp-section-help{font-size:.7rem;color:#85879A;margin-bottom:.75rem}
        .rp-table-head{background:#F2F0FF;border:1px solid #E1DCFF;border-radius:7px;padding:7px 4px;font-size:.64rem;font-weight:900;color:#3D326D;text-align:left;margin-bottom:2px}
        .rp-cell{min-height:42px;padding:8px 4px;border-bottom:1px solid #ECECF3;color:#34364D;font-size:.73rem;display:flex;align-items:center}
        .rp-q{font-weight:850;color:#211A4A}
        .rp-readonly{color:#55586E}
        .rp-summary-card{background:#fff;border:1px solid #E5E6EF;border-radius:9px;padding:12px;min-height:92px}
        .rp-summary-label{font-size:.65rem;font-weight:850;color:#7B7E91;letter-spacing:.02em}
        .rp-summary-value{font-size:1.28rem;font-weight:900;color:#211A4A;margin-top:8px}
        .rp-summary-sub{font-size:.65rem;color:#8B8D9E;margin-top:3px}
        .rp-note{background:#F7F6FF;border:1px solid #E4E0FF;border-radius:7px;padding:8px 10px;color:#6C6880;font-size:.68rem;margin:.45rem 0}
        .rp-edit-banner{background:#F4F1FF;border:1px solid #DED6FF;border-radius:8px;padding:9px 11px;color:#4C379A;font-size:.73rem;margin-bottom:.75rem}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_global_header(sb, user):
    name = student_name(sb, user)
    current = st.session_state.get("overview_level", "AS Level")
    c1, c2, c3 = st.columns([3.2, 2.2, 2.8])
    c1.markdown(f"<div class='rp-header-name'>{name}</div>", unsafe_allow_html=True)
    with c2:
        global_level = st.radio(
            "Global exam level",
            ["AS Level", "A Level"],
            index=0 if current == "AS Level" else 1,
            horizontal=True,
            key="rp_global_level",
            label_visibility="collapsed",
        )
        st.session_state.overview_level = global_level
    c3.markdown(f"<div class='rp-last'>◷ Last updated: {_last_updated(sb, user)}</div>", unsafe_allow_html=True)
    if c3.button("+ Record Practice Paper", type="primary", use_container_width=True, key="rp_new_action"):
        _reset_record_entry()
        st.rerun()


def _paper_details(sb):
    st.markdown("<div class='rp-section-title'>▣ Paper Details</div>", unsafe_allow_html=True)

    def clear_after_level():
        _clear(["rp_paper_type", "rp_session", "rp_variant"])

    def clear_after_type():
        _clear(["rp_session", "rp_variant"])

    def clear_after_session():
        _clear(["rp_variant"])

    default_level = "AS" if st.session_state.get("overview_level", "AS Level") == "AS Level" else "A"
    d1, d2, d3, d4, d5 = st.columns([.8, 2.0, 1.45, .8, 1.25])
    with d1:
        level = st.selectbox("Level *", ["AS", "A"], index=0 if default_level == "AS" else 1, key="rp_level", on_change=clear_after_level)
    db_level = "AS Level" if level == "AS" else "A Level"

    all_papers = get_df(sb, "exam_papers", "*", {"academic_level": db_level, "eligible": True})
    allowed = PAPER_TYPES[level]
    available_types = []
    for label, family in allowed.items():
        if not all_papers.empty and all_papers["paper_code"].map(_paper_family).eq(family).any():
            available_types.append(label)

    with d2:
        if available_types:
            paper_type = st.selectbox("Paper Type *", available_types, key="rp_paper_type", on_change=clear_after_type)
        else:
            st.selectbox("Paper Type *", ["No eligible paper types"], disabled=True, key="rp_no_paper_type")
            paper_type = None

    if not paper_type:
        with d3:
            st.selectbox("Session *", ["—"], disabled=True)
        with d4:
            st.selectbox("Variant *", ["—"], disabled=True)
        with d5:
            completed_on = st.date_input("Date Completed *", value=date.today(), max_value=date.today(), key="rp_date")
        return None, completed_on

    family = allowed[paper_type]
    subset = all_papers[all_papers["paper_code"].map(_paper_family) == family].copy()
    subset["session_label"] = subset.apply(_session_label, axis=1)
    session_options = sorted(subset["session_label"].unique().tolist(), reverse=True)
    with d3:
        session_label = st.selectbox("Session *", session_options, key="rp_session", on_change=clear_after_session)
    subset = subset[subset["session_label"] == session_label].copy()
    subset["variant"] = subset["paper_code"].map(_variant)
    variant_options = sorted(subset["variant"].unique().tolist())
    with d4:
        variant = st.selectbox("Variant *", variant_options, key="rp_variant")
    paper = subset[subset["variant"] == variant].iloc[0]

    existing = get_df(
        sb,
        "practice_attempts",
        "attempt_id,attempt_date",
        {"student_id": st.session_state.get("rp_user_id"), "paper_id": paper["paper_id"], "status": "completed"},
        order="updated_at",
        desc=True,
    ) if st.session_state.get("rp_user_id") else pd.DataFrame()
    default_date = pd.to_datetime(existing.iloc[0]["attempt_date"]).date() if not existing.empty else date.today()
    with d5:
        completed_on = st.date_input("Date Completed *", value=default_date, max_value=date.today(), key=f"rp_date_{paper['paper_id']}")
    return paper, completed_on


def _render_question_table(grid, prefix):
    st.markdown("<div class='rp-section-title'>▣ Question-level Performance</div>", unsafe_allow_html=True)
    st.markdown("<div class='rp-section-help'>Enter marks lost and error type for each question and sub-part.</div>", unsafe_allow_html=True)
    st.markdown("<div class='rp-note'>ⓘ Each row represents a question or sub-part. Topic, Sub-topic and Max Marks come from the question database.</div>", unsafe_allow_html=True)

    widths = [.42, .9, 1.35, 1.55, .75, .9, 1.65]
    headers = ["#", "Question", "Topic", "Sub-topic", "Max Marks", "Marks Lost", "Error Type"]
    header_cols = st.columns(widths)
    for col, text in zip(header_cols, headers):
        col.markdown(f"<div class='rp-table-head'>{text}</div>", unsafe_allow_html=True)

    rows = []
    for idx, source in grid.reset_index(drop=True).iterrows():
        cols = st.columns(widths)
        cols[0].markdown(f"<div class='rp-cell'>{idx + 1}</div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='rp-cell rp-q'>{source['Question']}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='rp-cell rp-readonly'>{source['Topic']}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='rp-cell rp-readonly'>{source['Sub-topic']}</div>", unsafe_allow_html=True)
        cols[4].markdown(f"<div class='rp-cell rp-readonly'>{int(float(source['Max Marks']))}</div>", unsafe_allow_html=True)

        initial_lost = "" if source.get("Marks Lost") is None or pd.isna(source.get("Marks Lost")) else str(int(source.get("Marks Lost")))
        lost_key = f"{prefix}_lost_{idx}"
        if lost_key not in st.session_state:
            st.session_state[lost_key] = initial_lost
        lost_text = cols[5].text_input("Marks Lost", key=lost_key, label_visibility="collapsed", placeholder="0")

        lost_value = None
        try:
            parsed = float(lost_text) if str(lost_text).strip() != "" else None
            if parsed is not None and parsed == int(parsed):
                lost_value = int(parsed)
        except Exception:
            pass

        error_key = f"{prefix}_error_{idx}"
        existing_error = source.get("Error Type")
        if lost_value == 0:
            st.session_state[error_key] = "No Error"
            error_type = cols[6].selectbox("Error Type", ["No Error"], key=error_key, disabled=True, label_visibility="collapsed")
        elif lost_value is not None and lost_value > 0:
            if st.session_state.get(error_key) not in ERROR_CHOICES:
                st.session_state[error_key] = existing_error if existing_error in ERROR_CHOICES else ERROR_CHOICES[0]
            error_type = cols[6].selectbox("Error Type", ERROR_CHOICES, key=error_key, label_visibility="collapsed")
        else:
            st.session_state.pop(error_key, None)
            error_type = None
            cols[6].selectbox("Error Type", ["Enter Marks Lost first"], disabled=True, key=f"{error_key}_disabled", label_visibility="collapsed")

        row = source.to_dict()
        row["Marks Lost"] = lost_text
        row["Error Type"] = error_type
        rows.append(row)
    return pd.DataFrame(rows)


def _results_summary(work):
    numeric = pd.to_numeric(work["Marks Lost"], errors="coerce")
    total_lost = float(numeric.fillna(0).sum())
    total_score = TOTAL_MARKS_MVP - total_lost
    percentage = total_score / TOTAL_MARKS_MVP * 100
    st.markdown("<div class='rp-section-title'>◷ Results Summary</div>", unsafe_allow_html=True)
    cards = st.columns(4)
    values = [
        ("TOTAL MARKS", "75", "out of 75"),
        ("TOTAL MARKS LOST", f"{total_lost:g}", "calculated"),
        ("TOTAL SCORE", f"{total_score:g} / 75", "calculated"),
        ("PERCENTAGE SCORE", f"{percentage:.1f}%", "calculated"),
    ]
    for col, (label, value, sub) in zip(cards, values):
        col.markdown(
            f"<div class='rp-summary-card'><div class='rp-summary-label'>{label}</div>"
            f"<div class='rp-summary-value'>{value}</div><div class='rp-summary-sub'>{sub}</div></div>",
            unsafe_allow_html=True,
        )
    return total_lost, total_score, percentage


def render_record_practice(sb, user):
    _practice_styles()
    st.session_state["rp_user_id"] = user.id
    _render_global_header(sb, user)
    st.markdown("<div class='rp-title'>Record Practice Paper</div>", unsafe_allow_html=True)
    st.markdown("<div class='rp-subtitle'>Enter your past-paper result to update your OneView progress.</div>", unsafe_allow_html=True)

    with st.container(border=True):
        paper, completed_on = _paper_details(sb)

    if paper is None:
        st.info("No eligible paper structure is available for the selected level. The question table will appear when a valid paper is available.")
        return

    existing = get_df(
        sb,
        "practice_attempts",
        "attempt_id,attempt_date",
        {"student_id": user.id, "paper_id": paper["paper_id"], "status": "completed"},
        order="updated_at",
        desc=True,
    )
    attempt_id = existing.iloc[0]["attempt_id"] if not existing.empty else None
    if attempt_id:
        st.markdown("<div class='rp-edit-banner'>Existing saved paper found. This page is in Edit/Correction mode; Update Practice Paper will modify the existing attempt and will not create a duplicate.</div>", unsafe_allow_html=True)

    with st.spinner("Loading question structure..."):
        grid = build_grid(sb, paper["paper_id"], attempt_id)
    if grid.empty:
        st.error("No valid paper structure is available. Saving is disabled.")
        return

    mapped_total = float(pd.to_numeric(grid["Max Marks"], errors="coerce").sum())
    if mapped_total != TOTAL_MARKS_MVP:
        st.error(f"This paper structure totals {mapped_total:g} marks. The Record Practice Paper MVP requires a 75-mark structure, so saving is disabled.")
        return

    prefix = f"rp_{paper['paper_id']}_{attempt_id or 'new'}"
    with st.container(border=True):
        work = _render_question_table(grid, prefix)

    with st.container(border=True):
        total_lost, total_score, percentage = _results_summary(work)

    errors = validate_grid(work, TOTAL_MARKS_MVP)
    for error in errors:
        st.error(error)

    cancel_col, save_col = st.columns([5, 1.8])
    if cancel_col.button("Cancel", use_container_width=True, key=f"{prefix}_cancel"):
        _reset_record_entry()
        st.session_state.nav = "Overview"
        st.rerun()

    action_label = "Update Practice Paper" if attempt_id else "Save Practice Paper"
    if save_col.button(action_label, type="primary", disabled=bool(errors), use_container_width=True, key=f"{prefix}_save"):
        try:
            score, pct, saved_attempt = save_attempt(sb, user, paper, work, completed_on, attempt_id)
            st.success(
                f"Practice paper {'updated' if attempt_id else 'saved'} successfully: {score:g}/75 ({pct:.1f}%). "
                "Overview and Topic Analysis data have been refreshed."
            )
            _reset_record_entry()
            st.session_state.nav = "Overview"
            st.rerun()
        except Exception as exc:
            st.error(f"Save failed. Your entries have been retained so you can retry. Details: {exc}")
