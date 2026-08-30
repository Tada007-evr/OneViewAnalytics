import streamlit as st

from overview_page import subject_panel, target_practice_dashboard


def render_overview(sb, user):
    """BRD Overview body. The shared global header is rendered once by main.py on every page."""
    st.session_state.setdefault("overview_level", "AS Level")
    level = st.session_state.overview_level

    st.markdown("<div class='brd-page-label'>OVERVIEW</div>", unsafe_allow_html=True)

    pure, stats = st.columns(2, gap="medium")
    with pure:
        subject_panel(sb, user, level, "Pure Mathematics")
    with stats:
        subject_panel(sb, user, level, "Statistics")

    target_practice_dashboard(sb, user, level)

    st.markdown(
        "<div class='oneview-footer'>Analytics are based on eligible saved practice papers with recorded questions and marks. "
        "Pure Mathematics and Statistics remain independent, and AS/A Level data are never mixed.</div>",
        unsafe_allow_html=True,
    )
