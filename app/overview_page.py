import pandas as pd
import streamlit as st

from bi_components import performance_trend
from oneview_db import get_df, overview_row, priorities, save_target, student_name


def fmt(value, digits=1):
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.{digits}f}".rstrip("0").rstrip(".")


def tag_class(status):
    if status in ("Target Achieved", "Improving", "Ahead of Target"):
        return "tag-green"
    if status in ("Behind Target", "Needs Focus", "High"):
        return "tag-red"
    if status in ("On Track", "Stable", "Medium"):
        return "tag-orange"
    return "tag-purple"


def metric_card(label, value, subtext, icon):
    st.markdown(
        f"<div class='brd-metric-card'>"
        f"<div class='brd-metric-icon'>{icon}</div>"
        f"<div class='brd-metric-label'>{label}</div>"
        f"<div class='brd-metric-value'>{value}</div>"
        f"<div class='brd-metric-sub'>{subtext}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )


@st.dialog("Edit Target")
def edit_target(sb, user, level, subject, row):
    available = int(row.get("available_papers") or 0)
    st.markdown(f"**{level} · {subject}**")
    st.markdown(
        f"<div class='dialog-available'><span>Available Papers</span><strong>{available}</strong></div>",
        unsafe_allow_html=True,
    )
    st.caption("The target is the intended number of papers to complete and cannot exceed Available Papers.")

    if available == 0:
        st.info("No eligible papers are available for this level and subject. Target setting is unavailable.")
        return
    if available < 15:
        st.warning(
            f"Minimum Target is 15 past papers. Available Papers is {available}, so a target cannot currently be saved."
        )
        return

    presets = get_df(sb, "overview_target_presets", "*", {"academic_level": level, "subject": subject})
    valid = presets[(presets["active"] == True) & (presets["target_value"] <= available)] if not presets.empty else pd.DataFrame()
    options = valid["target_type"].tolist() + ["Custom"]
    current_type = row.get("target_type")
    target_type = st.selectbox(
        "Target Type",
        options,
        index=options.index(current_type) if current_type in options else 0,
        help="Choose a configured target type or Custom. Target cannot exceed Available Papers.",
    )

    if target_type == "Custom":
        current = min(max(int(row.get("target_value") or 15), 15), available)
        target_value = st.number_input(
            "Custom Target",
            min_value=15,
            max_value=available,
            value=current,
            step=1,
            help="Whole-number paper count only. Minimum 15; maximum equals Available Papers.",
        )
    else:
        target_value = int(valid.loc[valid["target_type"] == target_type, "target_value"].iloc[0])
        st.markdown(
            f"<div class='target-preview'><span>Target</span><strong>{target_value} papers</strong></div>",
            unsafe_allow_html=True,
        )

    if st.button("Save Target", type="primary", use_container_width=True):
        try:
            save_target(sb, user.id, level, subject, target_type, target_value)
            st.success("Target saved.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def target_practice(sb, user, level, subject, row, show_edit=True):
    target = row.get("target_value")
    target_type = row.get("target_type") or "Not Set"
    completed = int(row.get("papers_completed") or 0)
    remaining = row.get("remaining")
    completion = row.get("completion_percentage")
    available = int(row.get("available_papers") or 0)
    status = row.get("target_status") or "Not Set"

    title_col, edit_col = st.columns([5.0, 1.2])
    title_col.markdown(
        "<div class='brd-section-title'>◎ TARGET PRACTICE "
        "<span title='The target is the intended number of papers to complete and cannot exceed available papers.'>ⓘ</span></div>",
        unsafe_allow_html=True,
    )
    title_col.markdown(f"<div class='brd-context'>{level} · {subject}</div>", unsafe_allow_html=True)
    if show_edit and edit_col.button("✎ Edit Target", key=f"target_dashboard_edit_{level}_{subject}", use_container_width=True):
        edit_target(sb, user, level, subject, row)

    cols = st.columns([1.45, 1, 1, 1, 1.25, 1.05])
    values = [
        ("TARGET TYPE", target_type),
        ("TARGET", "Not Set" if target is None or pd.isna(target) else str(int(target))),
        ("COMPLETED", str(completed)),
        ("REMAINING", "—" if remaining is None or pd.isna(remaining) else str(int(remaining))),
        ("% COMPLETION", "Not Set" if completion is None or pd.isna(completion) else f"{float(completion):.0f}%"),
        ("STATUS", status),
    ]
    for col, (label, value) in zip(cols, values):
        col.markdown(
            f"<div class='brd-target-cell'><div class='brd-target-label'>{label}</div>"
            f"<div class='brd-target-value'>{value}</div></div>",
            unsafe_allow_html=True,
        )

    progress = 0 if completion is None or pd.isna(completion) else min(max(float(completion), 0), 100) / 100
    st.progress(progress)
    st.markdown(
        f"<div class='brd-target-footer'>"
        f"<span class='tag {tag_class(status)}'>{status}</span>"
        f"<span>Available Papers: <strong>{available}</strong></span>"
        f"<span>Planning status only — target changes never alter historical performance.</span>"
        f"</div>",
        unsafe_allow_html=True,
    )


def target_practice_dashboard(sb, user, level):
    st.markdown("<div class='brd-page-label'>TARGET PRACTICE</div>", unsafe_allow_html=True)
    st.caption(
        "Set and track the intended number of eligible practice papers for the selected exam level and subject. "
        "This is a planning control and does not change historical attempts or academic performance metrics."
    )
    subject = st.segmented_control(
        "Target Practice Subject",
        ["Pure Mathematics", "Statistics"],
        default=st.session_state.get("target_practice_subject", "Pure Mathematics"),
        key="target_practice_subject",
        label_visibility="collapsed",
    )
    if subject is None:
        subject = "Pure Mathematics"
    row = overview_row(sb, user.id, level, subject)
    with st.container(border=True):
        target_practice(sb, user, level, subject, row, show_edit=True)


def trend_panel(sb, user, level, subject, status):
    attempts = get_df(
        sb,
        "v_overview_attempts",
        "attempt_date,percentage,paper_code",
        {"student_id": user.id, "academic_level": level, "subject": subject},
    )
    st.markdown("<div class='brd-subsection-title'>PERFORMANCE TREND</div>", unsafe_allow_html=True)
    if attempts.empty:
        st.info("More data needed")
        return
    st.plotly_chart(
        performance_trend(attempts, status),
        use_container_width=True,
        config={"displayModeBar": False},
    )
    if status == "More data needed":
        st.caption("More data needed")
    else:
        st.markdown(f"<span class='tag {tag_class(status)}'>{status}</span>", unsafe_allow_html=True)


def priority_panel(sb, user, level, subject):
    df = priorities(sb, user.id, level, subject)
    st.markdown("<div class='brd-subsection-title'>PRIORITY IMPROVEMENT AREAS</div>", unsafe_allow_html=True)
    if df.empty:
        st.info("More data needed")
        return

    for _, r in df.head(3).iterrows():
        priority = r["priority"]
        left, score, action = st.columns([4.4, 1.15, 0.8])
        left.markdown(
            f"<div class='brd-priority-row'><div class='brd-priority-topic'>{r['topic_name']}</div>"
            f"<div class='brd-priority-subtopic'>{r['subtopic_name']}</div></div>",
            unsafe_allow_html=True,
        )
        score.markdown(
            f"<div class='brd-priority-score'>{float(r['average_percentage']):.0f}%<br>"
            f"<span class='tag {tag_class(priority)}'>{priority}</span></div>",
            unsafe_allow_html=True,
        )
        if action.button("›", key=f"priority_{level}_{subject}_{r['priority_rank']}", help="Open Topic Analysis"):
            st.session_state.topic_subject = subject
            st.session_state.topic_name = r["topic_name"]
            st.session_state.subtopic_name = r["subtopic_name"]
            st.session_state.nav = "Topic Analysis"
            st.rerun()

    if st.button("View all in Topic Analysis →", key=f"topic_analysis_{level}_{subject}", use_container_width=True):
        st.session_state.topic_subject = subject
        st.session_state.nav = "Topic Analysis"
        st.rerun()


def narrative_cards(sb, user, level, subject):
    rows = get_df(
        sb,
        "v_overview_insight_recommendation",
        "insight_rule_id,insight_text,recommendation_rule_id,recommendation_text",
        {"student_id": user.id, "academic_level": level, "subject": subject},
    )
    row = rows.iloc[0] if not rows.empty else {}
    insight = row.get("insight_text") if hasattr(row, "get") else None
    insight_rule = row.get("insight_rule_id") if hasattr(row, "get") else "INS-05"
    recommendation = row.get("recommendation_text") if hasattr(row, "get") else None
    recommendation_rule = row.get("recommendation_rule_id") if hasattr(row, "get") else "REC-06"

    left, right = st.columns(2, gap="medium")
    with left:
        st.markdown(
            f"<div class='brd-narrative brd-insight' title='Rule: {insight_rule or 'INS-05'}'>"
            f"<div class='brd-narrative-title'>◉ ONEVIEW INSIGHT</div>"
            f"<div class='brd-narrative-text'>{insight or 'More practice data is needed before OneView can reliably assess this area.'}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with right:
        st.markdown(
            f"<div class='brd-narrative brd-recommendation' title='Rule: {recommendation_rule or 'REC-06'}'>"
            f"<div class='brd-narrative-title'>✎ RECOMMENDATION</div>"
            f"<div class='brd-narrative-text'>{recommendation or 'More relevant practice required; no weakness recommendation yet.'}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )


def subject_panel(sb, user, level, subject):
    row = overview_row(sb, user.id, level, subject)
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
            edit_target(sb, user, level, subject, row)

        m1, m2, m3 = st.columns(3)
        with m1:
            metric_card(
                "PAPERS COMPLETED",
                f"{completed} / {'—' if target is None or pd.isna(target) else int(target)}",
                "Target not set" if target is None or pd.isna(target) else f"{float(row.get('completion_percentage') or 0):.0f}% of target",
                "▣",
            )
        with m2:
            metric_card(
                "AVERAGE PERFORMANCE",
                "More data needed" if avg is None or pd.isna(avg) else f"{fmt(row.get('average_score'))}  {float(avg):.1f}%",
                "" if avg is not None and not pd.isna(avg) else "No valid attempts",
                "✦",
            )
        with m3:
            metric_card(
                "RECENT SCORE",
                "More data needed" if recent is None or pd.isna(recent) else f"{fmt(row.get('recent_score'),0)} / {fmt(row.get('recent_max_marks'),0)}",
                "No valid attempts" if recent is None or pd.isna(recent) else f"{float(recent):.1f}%",
                "↗",
            )

        st.markdown("<div class='brd-prediction-card'>", unsafe_allow_html=True)
        st.markdown("<div class='brd-prediction-label'>PREDICTED PERFORMANCE <span title='Transparent rule-based forecast using recent valid attempts.'>ⓘ</span></div>", unsafe_allow_html=True)
        if row.get("prediction_state") == "Sufficient":
            predicted_score = float(row.get("predicted_score") or 0)
            max_marks = float(row.get("predicted_max_marks") or 0)
            predicted_pct = float(row.get("predicted_percentage") or 0)
            st.markdown(
                f"<div class='brd-prediction-value'>{predicted_score:.0f} / {max_marks:.0f}</div>"
                f"<div class='brd-prediction-sub'>{predicted_pct:.1f}% · Rule-based forecast</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                "<div class='brd-prediction-value brd-empty'>More data needed</div>"
                "<div class='brd-prediction-sub'>A definitive prediction requires the configured minimum number of valid attempts.</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        trend_col, priority_col = st.columns(2, gap="medium")
        with trend_col:
            trend_panel(sb, user, level, subject, row.get("trend_status") or "More data needed")
        with priority_col:
            priority_panel(sb, user, level, subject)

        narrative_cards(sb, user, level, subject)


def render_overview(sb, user):
    name = student_name(sb, user)
    st.session_state.setdefault("overview_level", "AS Level")

    name_col, level_col, action_col = st.columns([3.6, 2.1, 2.7])
    name_col.markdown(f"<div class='brd-student-name'>{name}</div>", unsafe_allow_html=True)
    with level_col:
        level = st.radio(
            "Exam Level",
            ["AS Level", "A Level"],
            horizontal=True,
            key="overview_level",
            label_visibility="collapsed",
        )

    rows = get_df(sb, "v_bi_overview_dashboard", "last_updated", {"student_id": user.id, "academic_level": level})
    times = pd.to_datetime(rows["last_updated"], utc=True, errors="coerce") if not rows.empty else pd.Series(dtype="datetime64[ns, UTC]")
    if not times.empty:
        times = times[times.dt.year > 1970]
    updated = times.max().strftime("%d %b %Y, %I:%M %p") if not times.empty else "No activity yet"

    action_col.markdown(f"<div class='brd-last-updated'>◷ Last updated: {updated}</div>", unsafe_allow_html=True)
    if action_col.button("+ Record Practice Paper", type="primary", use_container_width=True):
        st.session_state.nav = "Record Practice Paper"
        st.rerun()

    st.markdown("<div class='brd-page-label'>OVERVIEW</div>", unsafe_allow_html=True)

    pure, stats = st.columns(2, gap="medium")
    with pure:
        subject_panel(sb, user, level, "Pure Mathematics")
    with stats:
        subject_panel(sb, user, level, "Statistics")

    # BRD Part C requires Target Practice to be visible within Overview below the top KPI/performance area.
    target_practice_dashboard(sb, user, level)

    st.markdown(
        "<div class='oneview-footer'>Analytics are based on eligible saved practice papers with recorded questions and marks. "
        "Pure Mathematics and Statistics remain independent, and AS/A Level data are never mixed.</div>",
        unsafe_allow_html=True,
    )
