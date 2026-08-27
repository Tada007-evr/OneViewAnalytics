import pandas as pd
import plotly.express as px
import streamlit as st
from oneview_db import get_df, overview_row, priorities, save_target, student_name

PURPLE = "#5B35D5"
DARK = "#211A4A"


def fmt(value, digits=1):
    if value is None or pd.isna(value):
        return "—"
    return f"{float(value):.{digits}f}".rstrip("0").rstrip(".")


def metric_card(label, value, sub=""):
    st.markdown(f"<div class='metric-card'><div class='metric-label'>{label}</div><div class='metric-value'>{value}</div><div class='metric-sub'>{sub}</div></div>", unsafe_allow_html=True)


def tag_class(status):
    if status in ("Target Achieved", "Improving", "Ahead of Target"):
        return "tag-green"
    if status in ("Behind Target", "Needs Focus"):
        return "tag-red"
    if status in ("On Track", "Stable"):
        return "tag-orange"
    return "tag-purple"


def insight_and_recommendation(row, priority_df):
    if int(row.get("papers_completed") or 0) < 5:
        return "INS-05", "More practice data is needed before OneView can reliably assess this area.", "REC-06", "More relevant practice required; no weakness recommendation yet."
    if priority_df.empty:
        return None, None, None, None
    p = priority_df.iloc[0]
    sub = p["subtopic_name"]
    if float(p.get("recent_error_frequency") or 0) >= 50:
        x, y = int(p.get("recent_error_count") or 0), int(p.get("recent_observation_count") or 0)
        return "INS-02", f"You have made errors in {sub} in {x} of your last {y} relevant attempts.", "REC-02", "Review recent errors; practise the same skill; reattempt similar questions."
    if p.get("subtopic_trend") == "Needs Focus":
        return "INS-03", f"Your recent performance in {sub} is declining.", "REC-03", "Targeted practice before the next full paper; review mistakes afterward."
    gap = float(p.get("performance_gap_pp") or 0)
    if gap >= 5:
        return "INS-01", f"{sub} is below your overall performance.", "REC-01", "Review the concept; practise targeted questions; reattempt similar past-paper questions."
    if p.get("subtopic_trend") == "Improving" and gap > 0:
        return "INS-04", f"Your performance in {sub} is improving, but it remains below your overall average.", "REC-05", "Continue targeted practice; reassess after more attempts."
    return None, None, None, None


@st.dialog("Edit Target")
def edit_target(sb, user, level, subject, row):
    available = int(row.get("available_papers") or 0)
    st.markdown(f"**{level} · {subject}**")
    st.write(f"Available Papers: **{available}**")
    st.caption("The target is the intended number of papers to complete and cannot exceed Available Papers.")
    if available < 15:
        st.warning(f"The MVP minimum target is 15 papers. Only {available} eligible paper(s) are currently available, so a target cannot yet be saved.")
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
    a, b, c, d = st.columns(4)
    a.metric("Target", "Not Set" if target is None or pd.isna(target) else int(target))
    b.metric("Completed", completed)
    c.metric("Remaining", "—" if remaining is None or pd.isna(remaining) else int(remaining))
    d.metric("% Completion", "Not Set" if completion is None or pd.isna(completion) else f"{float(completion):.0f}%")
    st.progress(0 if completion is None or pd.isna(completion) else min(float(completion) / 100, 1))
    st.markdown(f"<span class='tag {tag_class(status)}'>{status}</span> <span class='ov-muted'>Available Papers: {available}</span>", unsafe_allow_html=True)


def trend_panel(sb, user, level, subject, status):
    attempts = get_df(sb, "v_overview_attempts", "attempt_date,percentage,paper_code", {"student_id": user.id, "academic_level": level, "subject": subject})
    st.markdown("##### Performance Trend")
    if attempts.empty:
        st.info("More data needed")
        return
    attempts = attempts.sort_values("attempt_date").tail(8)
    fig = px.line(attempts, x="attempt_date", y="percentage", markers=True, hover_data=["paper_code"])
    fig.update_traces(line_color=PURPLE, marker_color=PURPLE)
    fig.update_layout(height=230, margin=dict(l=5,r=5,t=10,b=5), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", xaxis_title="", yaxis_title="", yaxis=dict(range=[0,100],gridcolor="#EEEFF5"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.markdown(f"<span class='tag {tag_class(status)}'>{status}</span>", unsafe_allow_html=True)


def priority_panel(sb, user, level, subject):
    df = priorities(sb, user.id, level, subject)
    st.markdown("##### Priority Improvement Areas")
    if df.empty:
        st.info("More data needed")
        return df
    for _, r in df.iterrows():
        c1, c2 = st.columns([4,1])
        cls = "tag-red" if r["priority"] == "High" else "tag-orange" if r["priority"] == "Medium" else "tag-purple"
        c1.markdown(f"<div class='priority-row'><div class='priority-title'>{r['topic_name']} · {r['subtopic_name']}</div><div class='priority-sub'>{float(r['average_percentage']):.1f}% · <span class='tag {cls}'>{r['priority']}</span></div></div>", unsafe_allow_html=True)
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
        h1, h2 = st.columns([4,1])
        icon = "ƒx" if subject == "Pure Mathematics" else "▥"
        h1.markdown(f"<div class='subject-title'><span style='color:{PURPLE}'>{icon}</span> {subject.upper()}</div>", unsafe_allow_html=True)
        h2.caption(level)
        target, completed = row.get("target_value"), int(row.get("papers_completed") or 0)
        avg, recent = row.get("average_percentage"), row.get("recent_percentage")
        c1, c2, c3 = st.columns(3)
        with c1:
            metric_card("Papers Completed", f"{completed} / {'—' if target is None or pd.isna(target) else int(target)}", "Target not set" if target is None or pd.isna(target) else f"{float(row.get('completion_percentage') or 0):.0f}% of target")
        with c2:
            metric_card("Average Performance", "More data needed" if avg is None or pd.isna(avg) else f"{float(avg):.1f}%", "No valid attempts" if avg is None or pd.isna(avg) else f"{fmt(row.get('average_score'))} average marks")
        with c3:
            metric_card("Recent Score", "More data needed" if recent is None or pd.isna(recent) else f"{fmt(row.get('recent_score'),0)} / {fmt(row.get('recent_max_marks'),0)}", "No valid attempts" if recent is None or pd.isna(recent) else f"{float(recent):.1f}%")
        st.markdown("##### Predicted Performance")
        if row.get("prediction_state") == "Sufficient":
            metric_card("Predicted Performance", f"{fmt(row.get('predicted_score'),0)} / {fmt(row.get('predicted_max_marks'),0)}", f"{float(row.get('predicted_percentage')):.1f}% · rule-based forecast")
        else:
            st.info("More data needed")
        target_panel(sb, user, level, subject, row)
        left, right = st.columns(2)
        with left:
            trend_panel(sb, user, level, subject, row.get("trend_status") or "More data needed")
        with right:
            p = priority_panel(sb, user, level, subject)
        ins_rule, insight, rec_rule, rec = insight_and_recommendation(row, p)
        i1, i2 = st.columns(2)
        with i1:
            st.markdown("##### ◉ OneView Insight")
            if insight:
                st.write(insight); st.caption(ins_rule)
            else:
                st.caption("No qualifying priority from the deterministic rules.")
        with i2:
            st.markdown("##### ✎ Recommendation")
            if rec:
                st.write(rec); st.caption(rec_rule)
            else:
                st.caption("No qualifying recommendation from the deterministic rules.")


def render_overview(sb, user):
    name = student_name(sb, user)
    st.session_state.setdefault("overview_level", "AS Level")
    c1, c2, c3 = st.columns([4,2.1,2.2])
    c1.markdown(f"<div class='ov-kicker'>OVERVIEW</div><div class='ov-title'>{name}</div>", unsafe_allow_html=True)
    with c2:
        level = st.radio("Exam Level", ["AS Level","A Level"], horizontal=True, key="overview_level", label_visibility="collapsed")
    rows = get_df(sb, "v_bi_overview_dashboard", "last_updated", {"student_id": user.id, "academic_level": level})
    times = pd.to_datetime(rows["last_updated"], utc=True, errors="coerce") if not rows.empty else pd.Series(dtype="datetime64[ns, UTC]")
    if not times.empty: times = times[times.dt.year > 1970]
    updated = times.max().strftime("%d %b %Y, %I:%M %p") if not times.empty else "No activity yet"
    c3.markdown(f"<div class='ov-muted' style='text-align:right'>Last updated: {updated}</div>", unsafe_allow_html=True)
    if c3.button("+ Record Practice Paper", type="primary", use_container_width=True):
        st.session_state.nav = "Record Practice Paper"; st.rerun()
    left, right = st.columns(2, gap="medium")
    with left: subject_panel(sb, user, level, "Pure Mathematics")
    with right: subject_panel(sb, user, level, "Statistics")
    st.markdown("<div class='oneview-footer'>Analytics use eligible saved practice papers with recorded questions and marks. AS and A Level data remain isolated.</div>", unsafe_allow_html=True)
