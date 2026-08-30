from datetime import date

import pandas as pd
import streamlit as st

from oneview_db import ERROR_TYPES, build_grid, calculate_practice_result, get_df, save_attempt, validate_grid

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
DATE_MIN = date(2020, 1, 1)


def _paper_family(code):
    text = str(code)
    return text.split("/", 1)[1][0] if "/" in text and len(text.split("/", 1)[1]) else ""


def _variant(code):
    text = str(code)
    return text.split("/", 1)[1] if "/" in text else text


def _session_label(row):
    return f"{row['session']} {int(row['year'])}"


def _clear(keys):
    for key in keys:
        st.session_state.pop(key, None)


def _reset_entry_widgets():
    for key in list(st.session_state.keys()):
        if str(key).startswith("rpv_"):
            st.session_state.pop(key, None)


def _styles():
    st.markdown(
        """
<style>
.rpv-title{font-size:1.58rem;font-weight:800;color:#111044;margin:.12rem 0 .12rem;letter-spacing:-.02em}
.rpv-subtitle{font-size:.72rem;color:#292845;margin-bottom:.9rem}
.rpv-section-title{font-size:.82rem;font-weight:800;color:#3526D7;margin:0 0 .12rem;display:flex;align-items:center;gap:.42rem}
.rpv-section-help{font-size:.66rem;color:#292845;margin-bottom:.6rem}
.rpv-info{background:#F6F7FF;border:0;border-radius:5px;padding:9px 12px;color:#33334E;font-size:.62rem;margin:.1rem 0 .65rem;text-align:right}
.rpv-edit{background:#F6F4FF;border:1px solid #DDD8FF;border-radius:7px;padding:8px 10px;color:#4C3BA4;font-size:.66rem;margin:.15rem 0 .55rem}
.rpv-th{background:#F1F3FA;border-top:1px solid #DDE0EA;border-bottom:1px solid #DDE0EA;padding:8px 6px;font-size:.60rem;font-weight:800;color:#17163A;min-height:38px;display:flex;align-items:center;justify-content:center}
.rpv-cell{border-bottom:1px solid #E7E8EF;padding:8px 6px;min-height:46px;display:flex;align-items:center;justify-content:center;font-size:.66rem;color:#17163A;line-height:1.2}
.rpv-question{font-weight:700;color:#17163A}
.rpv-summary{background:#fff;border:1px solid #E4E5ED;border-radius:7px;padding:13px 14px;min-height:94px}
.rpv-summary-label{font-size:.62rem;font-weight:500;color:#17163A;letter-spacing:0}
.rpv-summary-value{font-size:1.23rem;font-weight:800;color:#111044;margin-top:8px}
.rpv-summary-sub{font-size:.56rem;color:#31314B;margin-top:3px}
div[data-testid="stSelectbox"] label,div[data-testid="stDateInput"] label,div[data-testid="stTextInput"] label,div[data-testid="stNumberInput"] label{font-size:.63rem!important;font-weight:500!important;color:#17163A!important}
div[data-testid="stSelectbox"] [data-baseweb="select"]>div,div[data-testid="stDateInput"] input,div[data-testid="stTextInput"] input,div[data-testid="stNumberInput"] input{min-height:42px!important;font-size:.67rem!important;border-radius:5px!important;background:#fff!important;border-color:#D7D9E3!important;color:#17163A!important}
.rpv-actions .stButton>button{min-height:42px!important;font-size:.67rem!important}
</style>
""",
        unsafe_allow_html=True,
    )


def _paper_details(sb, user):
    st.markdown("<div class='rpv-section-title'>▣&nbsp; Paper Details</div>", unsafe_allow_html=True)

    def clear_after_level():
        _clear(["rpv_paper_type", "rpv_session", "rpv_variant"])

    def clear_after_type():
        _clear(["rpv_session", "rpv_variant"])

    def clear_after_session():
        _clear(["rpv_variant"])

    default_level = "AS" if st.session_state.get("overview_level", "AS Level") == "AS Level" else "A"
    d1, d2, d3, d4, d5 = st.columns([.75, 1.6, 1.25, .82, 1.18], gap="medium")
    with d1:
        level = st.selectbox("Level *", ["AS", "A"], index=0 if default_level == "AS" else 1, key="rpv_level", on_change=clear_after_level)
    db_level = "AS Level" if level == "AS" else "A Level"
    with d2:
        paper_type = st.selectbox("Paper Type *", list(PAPER_TYPES[level].keys()), key="rpv_paper_type", on_change=clear_after_type)

    family = PAPER_TYPES[level][paper_type]
    all_papers = get_df(sb, "exam_papers", "*", {"academic_level": db_level, "eligible": True})
    subset = all_papers[all_papers["paper_code"].map(_paper_family) == family].copy() if not all_papers.empty else pd.DataFrame()

    if subset.empty:
        with d3:
            st.selectbox("Session *", ["Not available"], disabled=True, key="rpv_no_session")
        with d4:
            st.selectbox("Variant *", ["—"], disabled=True, key="rpv_no_variant")
        with d5:
            completed_on = st.date_input("Date Completed *", value=date.today(), min_value=DATE_MIN, max_value=date.today(), key="rpv_date_empty")
        return None, completed_on

    subset["session_label"] = subset.apply(_session_label, axis=1)
    with d3:
        session_label = st.selectbox("Session *", sorted(subset["session_label"].unique().tolist(), reverse=True), key="rpv_session", on_change=clear_after_session)
    subset = subset[subset["session_label"] == session_label].copy()
    subset["variant"] = subset["paper_code"].map(_variant)
    with d4:
        variant = st.selectbox("Variant *", sorted(subset["variant"].unique().tolist()), key="rpv_variant")
    paper = subset[subset["variant"] == variant].iloc[0]

    existing = get_df(sb, "practice_attempts", "attempt_id,attempt_date", {"student_id": user.id, "paper_id": paper["paper_id"], "status": "completed"}, order="updated_at", desc=True)
    default_date = pd.to_datetime(existing.iloc[0]["attempt_date"]).date() if not existing.empty else date.today()
    default_date = max(default_date, DATE_MIN)
    with d5:
        completed_on = st.date_input("Date Completed *", value=default_date, min_value=DATE_MIN, max_value=date.today(), key=f"rpv_date_{paper['paper_id']}")
    return paper, completed_on


def _question_table(grid, prefix):
    title_col, info_col = st.columns([3.2, 1.8], vertical_alignment="center")
    title_col.markdown("<div class='rpv-section-title'>▣&nbsp; Question-level Performance</div>", unsafe_allow_html=True)
    title_col.markdown("<div class='rpv-section-help'>Enter marks lost and error type for each question and sub-part.</div>", unsafe_allow_html=True)
    info_col.markdown("<div class='rpv-info'>ⓘ&nbsp; Each row represents a question or sub-part.</div>", unsafe_allow_html=True)

    widths = [1.0, 1.45, 1.65, .72, .92, 1.7]
    headers = ["Question", "Topic", "Sub-topic", "Max Marks", "Marks Lost", "Error Type"]
    hcols = st.columns(widths, gap="small")
    for col, header in zip(hcols, headers):
        col.markdown(f"<div class='rpv-th'>{header}</div>", unsafe_allow_html=True)

    rows = []
    for idx, source in grid.reset_index(drop=True).iterrows():
        cols = st.columns(widths, gap="small")
        max_marks = int(float(source["Max Marks"]))
        cols[0].markdown(f"<div class='rpv-cell rpv-question'>{source['Question']}</div>", unsafe_allow_html=True)
        cols[1].markdown(f"<div class='rpv-cell'>{source['Topic']}</div>", unsafe_allow_html=True)
        cols[2].markdown(f"<div class='rpv-cell'>{source['Sub-topic']}</div>", unsafe_allow_html=True)
        cols[3].markdown(f"<div class='rpv-cell'>{max_marks}</div>", unsafe_allow_html=True)

        initial_lost = None if source.get("Marks Lost") is None or pd.isna(source.get("Marks Lost")) else int(source.get("Marks Lost"))
        lost_key = f"{prefix}_lost_{idx}"
        lost_value = cols[4].number_input("Marks Lost", min_value=0, max_value=max_marks, value=initial_lost, step=1, key=lost_key, label_visibility="collapsed", placeholder="0")

        error_key = f"{prefix}_error_{idx}"
        existing_error = source.get("Error Type")
        if lost_value == 0:
            st.session_state[error_key] = "No Error"
            error_type = cols[5].selectbox("Error Type", ["No Error"], key=error_key, disabled=True, label_visibility="collapsed")
        elif lost_value is not None and lost_value > 0:
            if st.session_state.get(error_key) == "No Error":
                st.session_state.pop(error_key, None)
            if error_key not in st.session_state and existing_error in ERROR_CHOICES:
                st.session_state[error_key] = existing_error
            error_type = cols[5].selectbox("Error Type", ERROR_CHOICES, index=None, key=error_key, placeholder="Select Error Type", label_visibility="collapsed")
        else:
            st.session_state.pop(error_key, None)
            error_type = None
            cols[5].selectbox("Error Type", ["Enter Marks Lost first"], disabled=True, key=f"{error_key}_disabled", label_visibility="collapsed")

        row = source.to_dict()
        row["Marks Lost"] = lost_value
        row["Error Type"] = error_type
        rows.append(row)

    st.markdown("<div style='font-size:.56rem;color:#4A4A63;margin-top:.5rem'>♙&nbsp; Error Type is locked as ‘No Error’ when Marks Lost is 0.</div>", unsafe_allow_html=True)
    return pd.DataFrame(rows)


def _summary(work):
    total_lost, total_score, percentage = calculate_practice_result(work, TOTAL_MARKS_MVP)
    st.markdown("<div class='rpv-section-title'>◷&nbsp; Results Summary</div>", unsafe_allow_html=True)
    cards = st.columns(4, gap="medium")
    values = [
        ("Total Marks", "75", "(out of 75)"),
        ("Total Marks Lost", f"{total_lost:g}", ""),
        ("Total Score", f"{total_score:g} / 75", ""),
        ("Percentage Score", f"{percentage:.1f}%", ""),
    ]
    for col, (label, value, sub) in zip(cards, values):
        col.markdown(f"<div class='rpv-summary'><div class='rpv-summary-label'>{label}</div><div class='rpv-summary-value'>{value}</div><div class='rpv-summary-sub'>{sub}</div></div>", unsafe_allow_html=True)
    return total_lost, total_score, percentage


def render_record_practice(sb, user):
    _styles()
    st.markdown("<div class='rpv-title'>Record Practice Paper</div>", unsafe_allow_html=True)
    st.markdown("<div class='rpv-subtitle'>Enter your past-paper result to update your OneView progress.</div>", unsafe_allow_html=True)

    flash = st.session_state.pop("rpv_flash", None)
    if flash:
        st.success(flash)

    with st.container(border=True):
        paper, completed_on = _paper_details(sb, user)

    if paper is None:
        st.info("No valid paper structure is loaded for this Paper Type. Session, Variant and question rows will become available when verified paper data is loaded.")
        return

    existing = get_df(sb, "practice_attempts", "attempt_id,attempt_date", {"student_id": user.id, "paper_id": paper["paper_id"], "status": "completed"}, order="updated_at", desc=True)
    attempt_id = existing.iloc[0]["attempt_id"] if not existing.empty else None
    if attempt_id:
        st.markdown("<div class='rpv-edit'>Existing saved paper opened in Edit/Correction mode. Update Practice Paper modifies this attempt and does not create a duplicate.</div>", unsafe_allow_html=True)

    with st.spinner("Loading question structure..."):
        grid = build_grid(sb, paper["paper_id"], attempt_id)
    if grid.empty:
        st.error("No valid paper structure is available. Saving is disabled.")
        return

    mapped_total = float(pd.to_numeric(grid["Max Marks"], errors="coerce").sum())
    if mapped_total != TOTAL_MARKS_MVP:
        st.error(f"This mapped paper totals {mapped_total:g} marks. The MVP requires 75, therefore saving is disabled.")
        return

    prefix = f"rpv_{paper['paper_id']}_{attempt_id or 'new'}"
    with st.container(border=True):
        work = _question_table(grid, prefix)

    with st.container(border=True):
        _summary(work)

    errors = validate_grid(work, TOTAL_MARKS_MVP)
    if completed_on < DATE_MIN:
        errors.append("Date Completed must be 01 Jan 2020 or later.")
    for error in errors:
        st.error(error)

    left, cancel_col, save_col = st.columns([5.6, 1.15, 1.65], gap="small")
    with cancel_col:
        if st.button("Cancel", use_container_width=True, key=f"{prefix}_cancel"):
            _reset_entry_widgets()
            st.session_state.nav = "Overview"
            st.rerun()

    action_label = "Update Practice Paper" if attempt_id else "Save Practice Paper"
    with save_col:
        if st.button(action_label, type="primary", disabled=bool(errors), use_container_width=True, key=f"{prefix}_save"):
            try:
                score, pct, _ = save_attempt(sb, user, paper, work, completed_on, attempt_id)
                st.session_state.rpv_flash = f"Practice paper {'updated' if attempt_id else 'saved'} successfully: {score:g}/75 ({pct:.1f}%). Overview and Topic Analysis data have been refreshed."
                _reset_entry_widgets()
                st.session_state.nav = "Record Practice Paper"
                st.rerun()
            except Exception as exc:
                st.error(f"Save failed. Your entries have been retained so you can retry. Details: {exc}")
