import html

import plotly.express as px
import streamlit as st

from oneview_db import get_df

BRD_BLUE = "#3526D7"
DARK = "#111044"


def _styles():
    st.markdown(
        f"""
        <style>
        .ta-title{{font-size:1.35rem;font-weight:900;color:{BRD_BLUE};margin:.05rem 0 .15rem;}}
        .ta-subtitle{{font-size:.66rem;color:#6F7187;margin-bottom:.65rem;}}
        .ta-section-label{{font-size:.70rem;font-weight:900;color:{BRD_BLUE};letter-spacing:.015em;margin:.25rem 0 .35rem;}}
        .ta-context{{font-size:.62rem;color:{DARK};margin:.10rem 0 .55rem;}}
        .ta-table-wrap{{border:1px solid #E3E4EE;border-radius:8px;overflow:hidden;background:#fff;margin:.15rem 0 .75rem;}}
        .ta-table{{width:100%;border-collapse:collapse;font-size:.62rem;}}
        .ta-table thead th{{background:#F1F0FF;color:{BRD_BLUE};font-weight:900;text-align:left;padding:8px 9px;border-bottom:1px solid #D9D6FA;white-space:nowrap;}}
        .ta-table tbody td{{color:{DARK};padding:7px 9px;border-bottom:1px solid #ECECF3;vertical-align:top;}}
        .ta-table tbody tr:last-child td{{border-bottom:0;}}
        .ta-filter-label{{font-size:.62rem;font-weight:800;color:{BRD_BLUE};margin-bottom:.15rem;}}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _table_html(view):
    headers = ["Topic", "Subtopic", "Observations", "Average %", "Recent Error %", "Trend"]
    rows = []
    for _, r in view.iterrows():
        cells = "".join(f"<td>{html.escape(str(r[h]))}</td>" for h in headers)
        rows.append(f"<tr>{cells}</tr>")
    head = "".join(f"<th>{h}</th>" for h in headers)
    return f"<div class='ta-table-wrap'><table class='ta-table'><thead><tr>{head}</tr></thead><tbody>{''.join(rows)}</tbody></table></div>"


def render_topic_analysis(sb, user):
    _styles()
    level = st.session_state.get("overview_level", "AS Level")

    st.markdown("<div class='ta-title'>Topic Analysis</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='ta-subtitle'>Detailed evidence and diagnostic view using the same eligible practice-paper data as Overview.</div>",
        unsafe_allow_html=True,
    )

    subject_default = st.session_state.get("topic_subject", "Pure Mathematics")
    st.markdown("<div class='ta-filter-label'>Subject</div>", unsafe_allow_html=True)
    subject = st.selectbox(
        "Subject",
        ["Pure Mathematics", "Statistics"],
        index=0 if subject_default == "Pure Mathematics" else 1,
        label_visibility="collapsed",
        key="topic_subject_filter",
    )
    st.markdown(f"<div class='ta-context'>Exam Level: <strong>{level}</strong></div>", unsafe_allow_html=True)

    df = get_df(
        sb,
        "v_overview_subtopic_performance",
        "*",
        {"student_id": user.id, "academic_level": level, "subject": subject},
    )
    if df.empty:
        st.info("More data needed")
        return

    if st.session_state.get("topic_name"):
        st.info(f"Priority context: {st.session_state.get('topic_name')} · {st.session_state.get('subtopic_name')}")

    view = df[["topic_name", "subtopic_name", "observation_count", "average_percentage", "recent_error_frequency", "subtopic_trend"]].copy()
    view.columns = ["Topic", "Subtopic", "Observations", "Average %", "Recent Error %", "Trend"]
    view = view.sort_values("Average %")

    st.markdown("<div class='ta-section-label'>SUBTOPIC PERFORMANCE</div>", unsafe_allow_html=True)
    st.markdown(_table_html(view), unsafe_allow_html=True)

    st.markdown("<div class='ta-section-label'>PERFORMANCE BY SUBTOPIC</div>", unsafe_allow_html=True)
    fig = px.bar(view, x="Average %", y="Subtopic", orientation="h", color="Topic")
    fig.update_layout(
        height=max(320, len(view) * 28),
        margin=dict(l=5, r=5, t=15, b=5),
        showlegend=False,
        font=dict(color=DARK),
        xaxis_title="Average %",
        yaxis_title="Subtopic",
    )
    fig.update_xaxes(title_font=dict(color=BRD_BLUE), tickfont=dict(color=DARK))
    fig.update_yaxes(title_font=dict(color=BRD_BLUE), tickfont=dict(color=DARK))
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption("Topic Analysis uses the same eligible practice-paper data and subtopic formulas as Overview.")
