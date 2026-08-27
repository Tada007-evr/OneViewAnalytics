import plotly.express as px
import streamlit as st
from oneview_db import get_df


def render_topic_analysis(sb, user):
    st.markdown("<div class='ov-kicker'>TOPIC ANALYSIS</div>", unsafe_allow_html=True)
    st.title("Topic Analysis")
    level = st.selectbox("Exam Level", ["AS Level", "A Level"], index=0 if st.session_state.get("overview_level", "AS Level") == "AS Level" else 1)
    subject_default = st.session_state.get("topic_subject", "Pure Mathematics")
    subject = st.selectbox("Subject", ["Pure Mathematics", "Statistics"], index=0 if subject_default == "Pure Mathematics" else 1)
    df = get_df(sb, "v_overview_subtopic_performance", "*", {
        "student_id": user.id, "academic_level": level, "subject": subject
    })
    if df.empty:
        st.info("More data needed")
        return
    if st.session_state.get("topic_name"):
        st.info(f"Priority context: {st.session_state.get('topic_name')} · {st.session_state.get('subtopic_name')}")
    view = df[["topic_name", "subtopic_name", "observation_count", "average_percentage", "recent_error_frequency", "subtopic_trend"]].copy()
    view.columns = ["Topic", "Subtopic", "Observations", "Average %", "Recent Error %", "Trend"]
    st.dataframe(view.sort_values("Average %"), hide_index=True, use_container_width=True)
    fig = px.bar(view.sort_values("Average %"), x="Average %", y="Subtopic", orientation="h", color="Topic")
    fig.update_layout(height=max(320, len(view) * 28), margin=dict(l=5, r=5, t=15, b=5), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption("Topic Analysis uses the same eligible practice-paper data and subtopic formulas as Overview.")
