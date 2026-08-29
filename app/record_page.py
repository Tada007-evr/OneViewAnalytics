from datetime import date

import pandas as pd
import streamlit as st

from oneview_db import ERROR_TYPES, build_grid, calculate_practice_result, get_df, save_attempt, student_name, validate_grid

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
        /* Finalized Record Practice Paper prototype, page 11 */
        .stApp{background:#ffffff!important;}
        .block-container{max-width:1160px!important;padding-top:.45rem!important;padding-bottom:2rem!important;}
        [data-testid="stSidebar"]{background:linear-gradient(180deg,#161361 0%,#29118D 58%,#211078 100%)!important;}
        [data-testid="stSidebar"] [data-baseweb="radio"] label{min-height:46px!important;border-radius:8px!important;margin:4px 0!important;}
        [data-testid="stSidebar"] [data-baseweb="radio"] label:has(input:checked){background:linear-gradient(90deg,#5B35D5,#734BEE)!important;box-shadow:0 5px 14px rgba(24,11,91,.24)!important;}

        .rp-topbar{border-bottom:1px solid #ECECF3;margin:-.1rem 0 1.2rem;padding:.2rem 0 .65rem;}
        .rp-title{font-size:1.62rem;font-weight:900;color:#1F2144;margin:.1rem 0 0;line-height:1.15;}
        .rp-subtitle{font-size:.78rem;color:#74778D;margin:.26rem 0 1.15rem;}
        .rp-header-name{font-size:.82rem;font-weight:800;color:#2B2D4B;padding-top:.52rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
        .rp-last{font-size:.68rem;color:#7E8092;text-align:right;padding:.32rem 0 .28rem;white-space:nowrap;}

        .rp-section-title{font-size:.84rem;font-weight:900;color:#5335D5;letter-spacing:.005em;margin:.05rem 0 .15rem;display:flex;align-items:center;gap:7px;}
        .rp-section-icon{display:inline-flex;width:23px;height:23px;border-radius:6px;align-items:center;justify-content:center;background:#EEE9FF;color:#5B35D5;font-size:.72rem;}
        .rp-section-help{font-size:.69rem;color:#85879A;margin:.08rem 0 .65rem;}
        .rp-hint{background:#F5F4FC;border-radius:6px;padding:7px 10px;color:#676A80;font-size:.64rem;text-align:center;}

        div[data-testid="stVerticalBlockBorderWrapper"]{border:1px solid #E8E8F0!important;border-radius:8px!important;background:#fff!important;box-shadow:0 1px 3px rgba(38,32,86,.035)!important;}
        div[data-testid="stVerticalBlockBorderWrapper"] > div{padding-top:.75rem!important;padding-bottom:.75rem!important;}

        .rp-table-head{background:#F1F0FB;border-top:1px solid #E3E1F2;border-bottom:1px solid #E3E1F2;padding:9px 7px;font-size:.62rem;font-weight:900;color:#44465E;text-align:left;margin-bottom:0;min-height:34px;}
        .rp-cell{min-height:46px;padding:12px 7px;border-bottom:1px solid #ECECF3;color:#42445B;font-size:.70rem;display:flex;align-items:center;background:#fff;}
        .rp-q{font-weight:850;color:#2C2E4B;}
        .rp-readonly{color:#565970;}
        .rp-note{background:#FAFAFE;border-top:1px solid #ECECF3;padding:8px 9px;color:#696B7D;font-size:.63rem;margin:.45rem 0 0;}
        .rp-edit-banner{background:#F5F2FF;border:1px solid #E0D9FF;border-radius:7px;padding:8px 10px;color:#4E389D;font-size:.69rem;margin:.45rem 0 .75rem;}

        .rp-summary-card{background:#fff;border:1px solid #E7E8EF;border-radius:7px;padding:12px 12px;min-height:100px;display:flex;gap:10px;align-items:flex-start;}
        .rp-summary-icon{width:30px;height:30px;min-width:30px;border-radius:999px;display:flex;align-items:center;justify-content:center;font-size:.85rem;font-weight:900;}
        .rp-icon-green{background:#E8F8F1;color:#14805A}.rp-icon-red{background:#FDEDEE;color:#D34D59}.rp-icon-blue{background:#EAF4FF;color:#3281D5}.rp-icon-purple{background:#F2EAFE;color:#6D43DD}
        .rp-summary-label{font-size:.61rem;font-weight:850;color:#7A7D90;letter-spacing:.015em;margin-top:1px;}
        .rp-summary-value{font-size:1.27rem;font-weight:900;color:#252744;margin-top:7px;line-height:1.05;}
        .rp-summary-sub{font-size:.61rem;color:#9698A7;margin-top:4px;}

        [data-testid="stTextInput"] input,[data-testid="stSelectbox"] > div > div,[data-testid="stDateInput"] input{border-color:#E3E4EC!important;border-radius:6px!important;min-height:39px!important;background:#fff!important;}
        [data-testid="stTextInput"] input:focus,[data-testid="stSelectbox"] > div > div:focus-within{border-color:#6A43DD!important;box-shadow:0 0 0 1px #6A43DD!important;}
        div[data-testid="stButton"] button[kind="primary"]{background:#5A30DA!important;border-color:#5A30DA!important;border-radius:6px!important;font-weight:800!important;}
        div[data-testid="stButton"] button[kind="secondary"]{border-color:#D7D8E2!important;background:#fff!important;border-radius:6px!important;color:#3E4057!important;}
        label[data-testid="stWidgetLabel"] p{font-size:.67rem!important;font-weight:750!important;color:#46495F!important;}
        .rp-actions{border-top:1px solid #ECECF3;margin-top:.3rem;padding-top:.7rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_global_header(sb, user):
    name = student_name(sb, user)
    current = st.session_state.get("overview_level", "AS Level")
    st.markdown("<div class='rp-topbar'>", unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns([2.25, 2.05, 2.25, 1.65], vertical_alignment="center")
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
    if c4.button("+ Record Practice Paper", type="primary", use_container_width=True, key="rp_new_action"):
        _reset_record_entry()
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


def _paper_details(sb):
    st.markdown("<div class='rp-section-title'><span class='rp-section-icon'>▣</span>Paper Details</div>", unsafe_allow_html=True)

    def clear_after_level():
        _clear(["rp_paper_type", "rp_session", "rp_variant"])

    def clear_after_type():
        _clear(["rp_session", "rp_variant"])

    def clear_after_session():
        _clear(["rp_variant"])

    default_level = "AS" if st.session_state.get("overview_level", "AS Level") == "AS Level" else "A"
    d1, d2, d3, d4, d5 = st.columns([.72, 1.95, 1.42, .76, 1.23], gap="small")
    with d1:
        level = st.selectbox("Level *", ["AS", "A"], index=0 if default_level == "AS" else 1, key="rp_level", on_change=clear_after_level)
    db_level = "AS Level" if level == "AS" else "A Level"

    # BRD RP-T-002 / RP-T-003: Paper Type list is determined by Level, not by whether data is currently loaded.
    allowed = PAPER_TYPES[level]
    with d2:
        paper_type = st.selectbox("Paper Type *", list(allowed.keys()), key="rp_paper_type", on_change=clear_after_type)

    family = allowed[paper_type]
    all_papers = get_df(sb, "exam_papers", "*", {"academic_level": db_level, "eligible": True})
    subset = all_papers[all_papers["paper_code"].map(_paper_family) == family].copy() if not all_papers.empty else pd.DataFrame()

    if subset.empty:
        with d3:
            st.selectbox("Session *", ["No available session"], disabled=True, key=f"rp_empty_session_{level}_{family}")
        with d4:
            st.selectbox("Variant *", ["—"], disabled=True, key=f"rp_empty_variant_{level}_{family}")
        with d5:
            completed_on = st.date_input("Date Completed *", value=date.today(), max_value=date.today(), key=f"rp_empty_date_{level}_{family}")
        return None, completed_on

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
    title_col, hint_col = st.columns([3.7, 2.0], vertical_alignment="center")
    title_col.markdown("<div class='rp-section-title'><span class='rp-section-icon'>▤</span>Question-level Performance</div>", unsafe_allow_html=True)
    hint_col.markdown("<div class='rp-hint'>ⓘ Each row represents a question or sub-part.</div>", unsafe_allow_html=True)
    st.markdown("<div class='rp-section-help'>Enter marks lost and error type for each question and sub-part.</div>", unsafe_allow_html=True)

    widths = [.38, .86, 1.25, 1.48, .7, .88, 1.58]
    headers = ["#", "Question", "Topic", "Sub-topic", "Max Marks", "Marks Lost", "Error Type"]
    header_cols = st.columns(widths, gap="small")
    for col, text in zip(header_cols, headers):
        col.markdown(f"<div class='rp-table-head'>{text}</div>", unsafe_allow_html=True)

    rows = []
    for idx, source in grid.reset_index(drop=True).iterrows():
        cols = st.columns(widths, gap="small", vertical_alignment="center")
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
            if st.session_state.get(error_key) == "No Error":
                st.session_state.pop(error_key, None)
            if error_key not in st.session_state and existing_error in ERROR_CHOICES:
                st.session_state[error_key] = existing_error
            error_type = cols[6].selectbox(
                "Error Type",
                ERROR_CHOICES,
                index=None,
                key=error_key,
                placeholder="Select error type",
                label_visibility="collapsed",
            )
        else:
            st.session_state.pop(error_key, None)
            error_type = None
            cols[6].selectbox("Error Type", ["Enter marks lost"], disabled=True, key=f"{error_key}_disabled", label_visibility="collapsed")

        row = source.to_dict()
        row["Marks Lost"] = lost_text
        row["Error Type"] = error_type
        rows.append(row)

    st.markdown("<div class='rp-note'>🔒 Error Type is locked to <b>No Error</b> when Marks Lost is 0.</div>", unsafe_allow_html=True)
    return pd.DataFrame(rows)


def _results_summary(work):
    total_lost, total_score, percentage = calculate_practice_result(work, TOTAL_MARKS_MVP)
    st.markdown("<div class='rp-section-title'><span class='rp-section-icon'>◔</span>Results Summary</div>", unsafe_allow_html=True)
    cards = st.columns(4, gap="small")
    values = [
        ("rp-icon-green", "▤", "Total Marks", "75", "out of 75"),
        ("rp-icon-red", "×", "Total Marks Lost", f"{total_lost:g}", "calculated"),
        ("rp-icon-blue", "◎", "Total Score", f"{total_score:g} / 75", "calculated"),
        ("rp-icon-purple", "%", "Percentage Score", f"{percentage:.1f}%", "calculated"),
    ]
    for col, (icon_class, icon, label, value, sub) in zip(cards, values):
        col.markdown(
            f"<div class='rp-summary-card'><div class='rp-summary-icon {icon_class}'>{icon}</div><div>"
            f"<div class='rp-summary-label'>{label}</div><div class='rp-summary-value'>{value}</div>"
            f"<div class='rp-summary-sub'>{sub}</div></div></div>",
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
        st.info("No eligible paper/session data is currently loaded for this Paper Type. Choose another valid Paper Type or load the authoritative paper data.")
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
        st.markdown("<div class='rp-edit-banner'>Existing saved paper found. Values are pre-populated for correction. Updating this paper will keep the same attempt and will not create a duplicate.</div>", unsafe_allow_html=True)

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

    st.markdown("<div class='rp-actions'></div>", unsafe_allow_html=True)
    spacer, cancel_col, save_col = st.columns([4.7, 1.0, 1.65], gap="small")
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