import pandas as pd
import streamlit as st

import overview_page as ov

BRD_BLUE = "#3526D7"
DARK = "#111044"


def _overview_brd_styles():
    st.markdown(
        f"""
        <style>
        .target-practice-heading{{font-size:.78rem;font-weight:900;color:{BRD_BLUE};letter-spacing:.015em;margin:.72rem 0 .08rem;}}
        .target-practice-help{{font-size:.58rem;color:#6F7187;margin:0 0 .42rem;}}
        .brd-section-title{{color:{BRD_BLUE}!important;font-size:.64rem!important;font-weight:900!important;letter-spacing:.02em!important;}}
        .brd-context{{color:{DARK}!important;font-size:.55rem!important;margin:.08rem 0 .35rem!important;}}
        .brd-target-cell{{min-height:62px;border-right:1px solid #E8E8F0;padding:5px 7px;}}
        .brd-target-label{{color:{BRD_BLUE}!important;font-size:.49rem!important;font-weight:900!important;letter-spacing:.025em!important;}}
        .brd-target-value{{color:{DARK}!important;font-size:.80rem!important;font-weight:900!important;margin-top:5px;}}
        .brd-target-footer{{display:flex;align-items:center;justify-content:space-between;gap:7px;color:#6F7187;font-size:.52rem;margin-top:3px;flex-wrap:wrap;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _subject_panel_brd(sb, user, level, subject):
    """Render the finalized Overview subject panel with BRD-exact Average Performance treatment."""
    row = ov.overview_row(sb, user.id, level, subject)
    target = row.get("target_value")
    completed = int(row.get("papers_completed") or 0)
    available = int(row.get("available_papers") or 0)
    avg = row.get("average_percentage")
    recent = row.get("recent_percentage")

    with st.container(border=True):
        head, edit = st.columns([4.4, 1.25])
        icon = "ƒx" if subject == "Pure Mathematics" else "▥"
        head.markdown(
            f"<div class='brd-subject-title'><span class='subject-icon'>{icon}</span>{subject.upper()}</div>"
            f"<div class='brd-subject-meta'>Practice Target: <strong>{'Not Set' if target is None or pd.isna(target) else int(target)}</strong> papers"
            f" &nbsp;•&nbsp; Available Papers: <strong>{available}</strong></div>",
            unsafe_allow_html=True,
        )
        if edit.button("✎ Edit Target", key=f"edit_{level}_{subject}", use_container_width=True):
            ov.edit_target(sb, user, level, subject, row)

        m1, m2, m3 = st.columns(3)
        with m1:
            ov.metric_card(
                "PAPERS COMPLETED",
                f"{completed} / {'—' if target is None or pd.isna(target) else int(target)}",
                "Target not set" if target is None or pd.isna(target) else f"{float(row.get('completion_percentage') or 0):.0f}% of target",
                "▣",
            )
        with m2:
            if avg is None or pd.isna(avg):
                avg_value = "More data needed"
                avg_subtext = "No valid attempts"
            else:
                assessment_max = row.get("recent_max_marks")
                avg_score = ov.fmt(row.get("average_score"))
                avg_value = avg_score if assessment_max is None or pd.isna(assessment_max) else f"{avg_score} / {ov.fmt(assessment_max, 0)}"
                avg_subtext = f"{float(avg):.1f}%"
            ov.metric_card("AVERAGE PERFORMANCE", avg_value, avg_subtext, "✦")
        with m3:
            ov.metric_card(
                "RECENT SCORE",
                "More data needed" if recent is None or pd.isna(recent) else f"{ov.fmt(row.get('recent_score'),0)} / {ov.fmt(row.get('recent_max_marks'),0)}",
                "No valid attempts" if recent is None or pd.isna(recent) else f"{float(recent):.1f}%",
                "↗",
            )

        st.markdown("<div class='brd-prediction-card'>", unsafe_allow_html=True)
        st.markdown("<div class='brd-prediction-label'>PREDICTED PERFORMANCE <span title='Transparent rule-based forecast using recent valid attempts.'>ⓘ</span></div>", unsafe_allow_html=True)
        if row.get("prediction_state") == "Sufficient":
            predicted_score = float(row.get("predicted_score") or 0)
            max_marks = float(row.get("predicted_max_marks") or 0)
            predicted_pct = float(row.get("predicted_percentage") or 0)
            st.markdown(f"<div class='brd-prediction-value'>{predicted_score:.0f} / {max_marks:.0f}</div><div class='brd-prediction-sub'>{predicted_pct:.1f}% · Rule-based forecast</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='brd-prediction-value brd-empty'>More data needed</div><div class='brd-prediction-sub'>A definitive prediction requires the configured minimum number of valid attempts.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        trend_col, priority_col = st.columns(2, gap="medium")
        with trend_col:
            ov.trend_panel(sb, user, level, subject, row.get("trend_status") or "More data needed")
        with priority_col:
            ov.priority_panel(sb, user, level, subject)
        ov.narrative_cards(sb, user, level, subject)


def render_overview(sb, user):
    """BRD Overview body. The shared global header is rendered once by main.py on every page."""
    _overview_brd_styles()
    st.session_state.setdefault("overview_level", "AS Level")
    level = st.session_state.overview_level
    st.markdown("<div class='brd-page-label'>OVERVIEW</div>", unsafe_allow_html=True)
    pure, stats = st.columns(2, gap="medium")
    with pure:
        _subject_panel_brd(sb, user, level, "Pure Mathematics")
    with stats:
        _subject_panel_brd(sb, user, level, "Statistics")
    st.markdown("<div class='target-practice-heading'>TARGET PRACTICE</div>", unsafe_allow_html=True)
    st.markdown("<div class='target-practice-help'>Target Type · Target · Completed · Remaining · % Completion · Status</div>", unsafe_allow_html=True)
    ov.target_practice_dashboard(sb, user, level)
    st.markdown("<div class='oneview-footer'>Analytics are based on eligible saved practice papers with recorded questions and marks. Pure Mathematics and Statistics remain independent, and AS/A Level data are never mixed.</div>", unsafe_allow_html=True)
