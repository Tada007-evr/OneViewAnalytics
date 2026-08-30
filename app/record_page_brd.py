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
.rpv-title{font-size:1.45rem;font-weight:900;color:#211A4A;margin:.05rem 0 .1rem}
.rpv-subtitle{font-size:.72rem;color:#808296;margin-bottom:.75rem}
.rpv-section-title{font-size:.78rem;font-weight:900;color:#5B35D5;margin:0 0 .08rem;display:flex;align-items:center;gap:.35rem}
.rpv-section-help{font-size:.66rem;color:#85879A;margin-bottom:.55rem}
.rpv-info{background:#F5F3FF;border:1px solid #E5DFFF;border-radius:6px;padding:7px 9px;color:#68647A;font-size:.64rem;margin:.2rem 0 .5rem}
.rpv-edit{background:#F5F2FF;border:1px solid #DDD5FF;border-radius:7px;padding:8px 10px;color:#533AA7;font-size:.68rem;margin:.15rem 0 .55rem}
.rpv-th{background:#F3F1FF;border-top:1px solid #E2DEFA;border-bottom:1px solid #E2DEFA;padding:7px 5px;font-size:.61rem;font-weight:900;color:#42386A;min-height:34px;display:flex;align-items:center}
.rpv-cell{border-bottom:1px solid #ECECF3;padding:7px 5px;min-height:42px;display:flex;align-items:center;font-size:.68rem;color:#45475C;line-height:1.2}
.rpv-question{font-weight:850;color:#252044}
.rpv-summary{background:#fff;border:1px solid #E5E6EF;border-radius:8px;padding:11px 12px;min-height:82px}
.rpv-summary-label{font-size:.59rem;font-weight:850;color:#7C7F91;letter-spacing:.025em}
.rpv-summary-value{font-size:1.18rem;font-weight:900;color:#211A4A;margin-top:7px}
.rpv-summary-sub{font-size:.6rem;color:#9193A2;margin-top:2px}
.rpv-card-gap{height:.15rem}
/* Compact widgets to mirror finalized prototype */
div[data-testid="stSelectbox"] label,div[data-testid="stDateInput"] label,div[data-testid="stTextInput"] label,div[data-testid="stNumberInput"] label{font-size:.64rem!important;font-weight:750!important;color:#49455F!important}
div[data-testid="stSelectbox"] [data-baseweb="select"]>div,div[data-testid="stDateInput"] input,div[data-testid="stTextInput"] input,div[data-testid="stNumberInput"] input{min-height:36px!important;font-size:.68rem!important}
.rpv-actions .stButton>button{min-height:38px!important;font-size:.7rem!important}
</style>
""",
        unsafe_allow_html=True,
    )


def _paper_details(sb, user):
    st.markdown("<div class='rpv-section-title'>▣ Paper Details</div>", unsafe_allow_html=True)

    def clear_after_level():
        _clear(["rpv_paper_type", "rpv_session", "rpv_variant"])

    def clear_after_type():
        _clear(["rpv_session", "rpv_variant"])

    def clear_after_session():
        _clear(["rpv_variant"])

    default_level = "AS" if st.session_state.get("overview_level", "AS Level") == "AS Level" else "A"
    d1, d2, d3, d4, d5 = st.columns([.75, 2.0, 1.5, .75, 1.2], gap="small")
    with d1:
        level = st.selectbox(
            "Level *", ["AS", "A"], index=0 if default_level == "AS" else 1,
            key="rpv_level", on_change=clear_after_level,
        )
    db_level = "AS Level" if level == "AS" else "A Level"

    with d2:
        paper_type = st.selectbox(
            "Paper Type *", list(PAPER_TYPES[level].keys()),
            key="rpv_paper_type", on_change=clear_after_type,
        )

    family = PAPER_TYPES[level][paper_type]
    all_papers = get_df(sb, "exam_papers", "*", {"academic_level": db_level, "eligible": True})
    subset = all_papers[all_papers["paper_code"].map(_paper_family) == family].copy() if not all_papers.empty else pd.DataFrame()

    if subset.empty:
        with d3:
            st.selectbox("Session *", ["Not available"], disabled=True, key="rpv_no_session")
        with d4:
            st.selectbox("Variant *", ["—"], disabled=True, key="rpv_no_variant")
        with d5:
            completed_on = st.date_input(
                "Date Completed *",
                value=date.today(),
                min_value=DATE_MIN,
                max_value=date.today(),
                key="rpv_date_empty",
            )
        return None, completed_on

    subset["session_label"] = subset.apply(_session_label, axis=1)
    with d3:
        session_label = st.selectbox(
            "Session *", sorted(subset["session_label"].unique().tolist(), reverse=True),
            key="rpv_session", on_change=clear_after_session,
        )
    subset = subset[subset["session_label"] == session_label].copy()
    subset["variant"] = subset["paper_code"].map(_variant)
    with d4:
        variant = st.selectbox("Variant *", sorted(subset["variant"].unique().tolist()), key="rpv_variant")
    paper = subset[subset["variant"] == variant].iloc[0]

    existing = get_df(
        sb, "practice_attempts", "attempt_id,attempt_date", {
            "student_id": user.id, "paper_id": paper["paper_id"], "status": "completed"
        }, order="updated_at", desc=True,
    )
    default_date = pd.to_datetime(existing.iloc[0]["attempt_date"]).date() if not existing.empty else date.today()
    default_date = max(default_date, DATE_MIN)
    with d5:
        completed_on = st.date_input(
            "Date Completed *",
            value=default_date,
            min_value=DATE_MIN,
            max_value=date.today(),
            key=f"rpv_date_{paper['paper_id']}",
        )
    return paper, completed_on


def _question_table(grid, prefix):
    st.markdown("<div class='rpv-section-title'>▣ Question-level Performance</div>", unsafe_allow_html=True)
    st.markdown("<div class='rpv-section-help'>Enter marks lost and error type for each question and sub-part.</div>", unsafe_allow_html=True)
    st.markdown("<div class='rpv-info'>ⓘ Each row represents a question or sub-part. Topic, Sub-topic and Max Marks are read-only and come from the question database.</div>", unsafe_allow_html=True)

    # User-requested removal of the prototype's display-only # column.
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
        lost_value = cols[4].number_input(
            "Marks Lost",
            min_value=0,
            max_value=max_marks,
            value=initial_lost,
            step=1,
            key=lost_key,
            label_visibility="collapsed",
            placeholder="0",
        )

        error_key = f"{prefix}_error_{idx}"
        existing_error = source.get("Error Type")
        if lost_value == 0:
            st.session_state[error_key] = "No Error"
            error_type = cols[5].selectbox(
                "Error Type", ["No Error"], key=error_key, disabled=True,
                label_visibility="collapsed",
            )
        elif lost_value is not None and lost_value > 0:
            if st.session_state.get(error_key) == "No Error":
                st.session_state.pop(error_key, None)
            if error_key not in st.session_state and existing_error in ERROR_CHOICES:
                st.session_state[error_key] = existing_error
            error_type = cols[5].selectbox(
                "Error Type", ERROR_CHOICES, index=None, key=error_key,
                placeholder="Select Error Type", label_visibility="collapsed",
            )
        else:
            st.session_state.pop(error_key, None)
            error_type = None
            cols[5].selectbox(
                "Error Type", ["Enter Marks Lost first"], disabled=True,
                key=f"{error_key}_disabled", label_visibility="collapsed",
            )

        row = source.to_dict()
        row["Marks Lost"] = lost_value
        row["Error Type"] = error_type
        rows.append(row)
    return pd.DataFrame(rows)


def _summary(work):
    total_lost, total_score, percentage = calculate_practice_result(work, TOTAL_MARKS_MVP)
    st.markdown("<div class='rpv-section-title'>◷ Results Summary</div>", unsafe_allow_html=True)
    cards = st.columns(4, gap="small")
    values = [
        ("TOTAL MARKS", "75", "out of 75"),
        ("TOTAL MARKS LOST", f"{total_lost:g}", "calculated"),
        ("TOTAL SCORE", f"{total_score:g} / 75", "calculated"),
        ("PERCENTAGE SCORE", f"{percentage:.1f}%", "calculated"),
    ]
    for col, (label, value, sub) in zip(cards, values):
        col.markdown(
            f"<div class='rpv-summary'><div class='rpv-summary-label'>{label}</div>"
            f"<div class='rpv-summary-value'>{value}</div><div class='rpv-summary-sub'>{sub}</div></div>",
            unsafe_allow_html=True,
        )
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

    existing = get_df(
        sb, "practice_attempts", "attempt_id,attempt_date", {
            "student_id": user.id, "paper_id": paper["paper_id"], "status": "completed"
        }, order="updated_at", desc=True,
    )
    attempt_id = existing.iloc[0]["attempt_id"] if not existing.empty else None
    if attempt_id:
        st.markdown(
            "<div class='rpv-edit'>Existing saved paper opened in Edit/Correction mode. Update Practice Paper modifies this attempt and does not create a duplicate.</div>",
            unsafe_allow_html=True,
        )

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
        if st.button(
            action_label, type="primary", disabled=bool(errors),
            use_container_width=True, key=f"{prefix}_save",
        ):
            try:
                score, pct, _ = save_attempt(sb, user, paper, work, completed_on, attempt_id)
                # Explicit user requirement: remain on Record Practice Paper after save/update.
                st.session_state.rpv_flash = (
                    f"Practice paper {'updated' if attempt_id else 'saved'} successfully: "
                    f"{score:g}/75 ({pct:.1f}%). Overview and Topic Analysis data have been refreshed."
                )
                _reset_entry_widgets()
                st.session_state.nav = "Record Practice Paper"
                st.rerun()
            except Exception as exc:
                st.error(f"Save failed. Your entries have been retained so you can retry. Details: {exc}")
