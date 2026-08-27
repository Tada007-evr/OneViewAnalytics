import pandas as pd
import streamlit as st

from bi_components import completion_donut, performance_gauge, performance_trend, prediction_band, priority_bar
from oneview_db import get_df, overview_row, priorities, save_target, student_name

PURPLE = "#5B35D5"
DARK = "#211A4A"


def fmt(value, digits=1):
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.{digits}f}".rstrip("0").rstrip(".")


def metric_card(label, value, sub="", icon=""):
    icon_html = f"<span class='metric-icon'>{icon}</span>" if icon else ""
    st.markdown(
        f"<div class='metric-card'>{icon_html}<div class='metric-label'>{label}</div>"
        f"<div class='metric-value'>{value}</div><div class='metric-sub'>{sub}</div></div>",
        unsafe_allow_html=True,
    )


def tag_class(status):
    if status in ("Target Achieved", "Improving", "Ahead of Target"):
        return "tag-green"
    if status in ("Behind Target", "Needs Focus"):
        return "tag-red"
    if status in ("On Track", "Stable"):
        return "tag-orange"
    return "tag-purple"


@st.dialog("Edit Target")
def edit_target(sb, user, level, subject, row):
    available = int(row.get("available_papers") or 0)
    st.markdown(f"**{level} · {subject}**")
    st.markdown(f"<div class='dialog-available'>Available Papers <strong>{available}</strong></div>", unsafe_allow_html=True)
    st.caption("The target is the intended number of papers to complete and cannot exceed Available Papers.")
    if available < 15:
        st.warning(
            f"The MVP minimum target is 15 papers. Only {available} eligible paper(s) are currently available, "
            "so a target cannot yet be saved."
        )
        return
    presets = get_df(sb, "overview_target_presets", "*", {"academic_level": level, "subject": subject})
    valid = presets[(presets["active"] == True) & (presets["target_value"] <= available)] if not presets.empty else pd.DataFrame()
    options = valid["target_type"].tolist() + ["Custom"]
    current_type = row.get("target_type")
    target_type = st.selectbox("Target Type", options, index=options.index(current_type) if current_type in options else 0)
    if target_type == "Custom":
        current = min(max(int(row.get("target_value") or 15), 15), available)
        target_value = st.number_input("Custom Target", min_value=15, max_value=available, value=current, step=1)
    else:
        target_value = int(valid.loc[valid["target_type"] == target_type, "target_value"].iloc[0])
        st.metric("Target", target_value)
    if st.button("Save Target", type="primary", use_container_width=True):
        try:
            save_target(sb, user.id, level, subject, target_type, target_value)
            st.success("Target saved.")
            st.rerun()
        except Exception as exc:
            st.error(str(exc))


def target_panel(sb, user, level, subject, row):
    available = int(row.get("available_papers") or 0)
    completed = int(row.get("papers_completed") or 0)
    target, remaining, completion = row.get("target_value"), row.get("remaining"), row.get("completion_percentage")
    status = row.get("target_status") or "Not Set"

    h1, h2 = st.columns([4, 1])
    h1.markdown("#### Target Practice")
    if h2.button("✎ Edit Target", key=f"edit_{level}_{subject}", use_container_width=True):
        edit_target(sb, user, level, subject, row)

    ring, facts = st.columns([1.05, 1.95])
    with ring:
        st.plotly_chart(completion_donut(completion, completed, target), use_container_width=True, config={"displayModeBar": False})
    with facts:
        a, b = st.columns(2)
        a.metric("Target", "Not Set" if target is None or pd.isna(target) else int(target))
        b.metric("Available", available)
        c, d = st.columns(2)
        c.metric("Completed", completed)
        d.metric("Remaining", "—" if remaining is None or pd.isna(remaining) else int(remaining))
        st.markdown(
            f"<span class='tag {tag_class(status)}'>{status}</span>"
            f" <span class='ov-muted'>Planning status only</span>", unsafe_allow_html=True
        )


def trend_panel(sb, user, level, subject, status):
    attempts = get_df(
        sb, "v_overview_attempts", "attempt_date,percentage,paper_code",
        {"student_id": user.id, "academic_level": level, "subject": subject},
    )
    st.markdown("##### Performance Trend")
    if attempts.empty:
        st.info("More data needed")
        return
    st.plotly_chart(performance_trend(attempts, status), use_container_width=True, config={"displayModeBar": False})
    st.markdown(f"<span class='tag {tag_class(status)}'>{status}</span>", unsafe_allow_html=True)


def priority_panel(sb, user, level, subject):
    df = priorities(sb, user.id, level, subject)
    st.markdown("##### Priority Improvement Areas")
    if df.empty:
        st.info("More data needed")
        return df

    fig = priority_bar(df)
    if fig is not None:
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    for _, r in df.iterrows():
        c1, c2 = st.columns([4, 1])
        cls = "tag-red" if r["priority"] == "High" else "tag-orange" if r["priority"] == "Medium" else "tag-purple"
        c1.markdown(
            f"<div class='priority-row'><div class='priority-title'>{r['topic_name']} · {r['subtopic_name']}</div>"
            f"<div class='priority-sub'>{float(r['average_percentage']):.1f}% · "
            f"<span class='tag {cls}'>{r['priority']}</span></div></div>", unsafe_allow_html=True
        )
        if c2.button("View", key=f"priority_{subject}_{r['priority_rank']}", use_container_width=True):
            st.session_state.topic_subject = subject
            st.session_state.topic_name = r["topic_name"]
            st.session_state.subtopic_name = r["subtopic_name"]
            st.session_state.nav = "Topic Analysis"
            st.rerun()
    return df


def subject_panel(sb, user, level, subject):
    row = overview_row(sb, user.id, level, subject)
    with st.container(border=True):
        h1, h2 = st.columns([4, 1])
        icon = "ƒx" if subject == "Pure Mathematics" else "▥"
        h1.markdown(
            f"<div class='subject-title'><span class='subject-icon'>{icon}</span> {subject.upper()}</div>",
            unsafe_allow_html=True,
        )
        h2.markdown(f"<div class='level-pill'>{level}</div>", unsafe_allow_html=True)

        target, completed = row.get("target_value"), int(row.get("papers_completed") or 0)
        avg, recent = row.get("average_percentage"), row.get("recent_percentage")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card(
                "Papers Completed",
                f"{completed} / {'—' if target is None or pd.isna(target) else int(target)}",
                "Target not set" if target is None or pd.isna(target) else f"{float(row.get('completion_percentage') or 0):.0f}% of target",
                "✓",
            )
        with c2:
            metric_card(
                "Average Performance",
                "More data needed" if avg is None or pd.isna(avg) else f"{float(avg):.1f}%",
                "No valid attempts" if avg is None or pd.isna(avg) else f"{fmt(row.get('average_score'))} average marks",
                "↗",
            )
        with c3:
            metric_card(
                "Recent Score",
                "More data needed" if recent is None or pd.isna(recent) else f"{fmt(row.get('recent_score'),0)} / {fmt(row.get('recent_max_marks'),0)}",
                "No valid attempts" if recent is None or pd.isna(recent) else f"{float(recent):.1f}%",
                "●",
            )

        visual_a, visual_b = st.columns([1, 1.45])
        with visual_a:
            gauge = performance_gauge(avg)
            if gauge is None:
                st.markdown("##### Average Performance")
                st.info("More data needed")
            else:
                st.plotly_chart(gauge, use_container_width=True, config={"displayModeBar": False})
        with visual_b:
            st.markdown("##### Predicted Performance")
            if row.get("prediction_state") == "Sufficient":
                band = prediction_band(row.get("predicted_percentage"), recent)
                st.plotly_chart(band, use_container_width=True, config={"displayModeBar": False})
                st.caption(
                    f"{fmt(row.get('predicted_score'),0)} / {fmt(row.get('predicted_max_marks'),0)} · "
                    f"{float(row.get('predicted_percentage')):.1f}% · rule-based forecast"
                )
            else:
                st.info("More data needed")
                st.caption("Prediction requires sufficient valid completed attempts.")

        target_panel(sb, user, level, subject, row)
        left, right = st.columns(2)
        with left:
            trend_panel(sb, user, level, subject, row.get("trend_status") or "More data needed")
        with right:
            p = priority_panel(sb, user, level, subject)

        insight_rows = get_df(
            sb,
            "v_overview_insight_recommendation",
            "insight_rule_id,insight_text,recommendation_rule_id,recommendation_text",
            {"student_id": user.id, "academic_level": level, "subject": subject},
        )
        insight_row = insight_rows.iloc[0] if not insight_rows.empty else {}
        i1, i2 = st.columns(2)
        with i1:
            st.markdown("<div class='narrative-card narrative-insight'><div class='narrative-kicker'>ONEVIEW INSIGHT</div>", unsafe_allow_html=True)
            insight = insight_row.get("insight_text") if hasattr(insight_row, "get") else None
            rule = insight_row.get("insight_rule_id") if hasattr(insight_row, "get") else None
            st.write(insight or "More practice data is needed before OneView can reliably assess this area.")
            st.caption(rule or "INS-05")
            st.markdown("</div>", unsafe_allow_html=True)
        with i2:
            st.markdown("<div class='narrative-card narrative-rec'><div class='narrative-kicker'>RECOMMENDATION</div>", unsafe_allow_html=True)
            rec = insight_row.get("recommendation_text") if hasattr(insight_row, "get") else None
            rec_rule = insight_row.get("recommendation_rule_id") if hasattr(insight_row, "get") else None
            st.write(rec or "More relevant practice required; no weakness recommendation yet.")
            st.caption(rec_rule or "REC-06")
            st.markdown("</div>", unsafe_allow_html=True)


def render_overview(sb, user):
    name = student_name(sb, user)
    st.session_state.setdefault("overview_level", "AS Level")
    c1, c2, c3 = st.columns([4, 2.1, 2.2])
    c1.markdown(
        f"<div class='ov-kicker'>OVERVIEW DASHBOARD</div><div class='ov-title'>{name}</div>"
        "<div class='ov-muted'>Performance, priorities and next actions in one view</div>",
        unsafe_allow_html=True,
    )
    with c2:
        level = st.radio(
            "Exam Level", ["AS Level", "A Level"], horizontal=True,
            key="overview_level", label_visibility="collapsed"
        )
    rows = get_df(sb, "v_bi_overview_dashboard", "last_updated", {"student_id": user.id, "academic_level": level})
    times = pd.to_datetime(rows["last_updated"], utc=True, errors="coerce") if not rows.empty else pd.Series(dtype="datetime64[ns, UTC]")
    if not times.empty:
        times = times[times.dt.year > 1970]
    updated = times.max().strftime("%d %b %Y, %I:%M %p") if not times.empty else "No activity yet"
    c3.markdown(f"<div class='ov-muted' style='text-align:right'>Last updated<br><strong>{updated}</strong></div>", unsafe_allow_html=True)
    if c3.button("+ Record Practice Paper", type="primary", use_container_width=True):
        st.session_state.nav = "Record Practice Paper"
        st.rerun()

    st.markdown("<div class='section-rule'></div>", unsafe_allow_html=True)
    left, right = st.columns(2, gap="large")
    with left:
        subject_panel(sb, user, level, "Pure Mathematics")
    with right:
        subject_panel(sb, user, level, "Statistics")
    st.markdown(
        "<div class='oneview-footer'>Analytics use eligible saved practice papers with recorded questions and marks. "
        "AS and A Level data remain isolated. All Overview and BI visuals use the same Supabase semantic views.</div>",
        unsafe_allow_html=True,
    )
