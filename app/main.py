import os

import pandas as pd
import streamlit as st
from supabase import create_client

from oneview_db import get_df, student_name
from overview_page import render_overview
from record_page import render_record_practice
from topic_page import render_topic_analysis

st.set_page_config(
    page_title="OneView Learning Analytics",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

PURPLE = "#5B35D5"
DARK = "#211A4A"
MUTED = "#777A91"
NAVY = "#22106F"

st.markdown(
    f"""
<style>
:root {{ --ov-purple:{PURPLE}; --ov-dark:{DARK}; --ov-muted:{MUTED}; }}
.stApp {{ background:#F7F8FC; color:#20213A; }}
.block-container {{ max-width:1420px; padding-top:.55rem; padding-bottom:1.5rem; padding-left:1.35rem; padding-right:1.35rem; }}

/* BRD compact left navigation */
[data-testid="stSidebar"] {{
  background:linear-gradient(180deg,#20106A 0%,#29117E 52%,#25106E 100%);
  border-right:0;
  min-width:188px !important;
  max-width:188px !important;
  width:188px !important;
}}
[data-testid="stSidebar"] > div:first-child {{ width:188px !important; }}
[data-testid="stSidebar"] * {{ color:white; }}
[data-testid="stSidebar"] .stButton > button {{
  width:100%; min-height:42px; border:0; border-radius:7px; box-shadow:none;
  justify-content:flex-start; text-align:left; font-size:.78rem; font-weight:650;
  padding:.55rem .7rem; margin:.08rem 0; color:#F5F3FF;
  background:transparent;
}}
[data-testid="stSidebar"] .stButton > button:hover {{ background:#38208C; color:white; border:0; }}
[data-testid="stSidebar"] .stButton > button[kind="primary"] {{
  background:#5B35D5 !important; color:white !important; border:0 !important;
}}
.nav-brand {{ font-size:.92rem; font-weight:900; letter-spacing:.035em; padding:.15rem 0 0; }}
.nav-sub {{ font-size:.62rem; color:#CFC8FF; margin-bottom:1rem; }}
.nav-user {{ font-size:.74rem; font-weight:800; color:white; }}
.nav-email {{ font-size:.59rem; color:#CBC5EF; word-break:break-all; }}

/* Shared global header from finalized prototypes */
.global-header {{ margin-bottom:.4rem; }}
.brd-student-name {{ font-size:.88rem; font-weight:850; color:{DARK}; padding-top:.48rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.brd-last-updated {{ text-align:right; color:{MUTED}; font-size:.66rem; padding:.48rem 0 .22rem; white-space:nowrap; }}
[data-testid="stSegmentedControl"] button {{ font-size:.69rem !important; min-height:32px !important; padding:.2rem .65rem !important; }}
.brd-page-label {{ color:{PURPLE}; font-size:.7rem; font-weight:900; letter-spacing:.06em; margin:.5rem 0 .65rem; }}

.brd-subject-title {{ font-size:.98rem; font-weight:900; color:{DARK}; display:flex; align-items:center; gap:7px; }}
.subject-icon {{ width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; border-radius:7px; background:#EFEAFF; color:{PURPLE}; font-weight:900; }}
.brd-subject-meta {{ color:{MUTED}; font-size:.72rem; margin:.26rem 0 .65rem; }}
.brd-metric-card {{ position:relative; min-height:105px; background:#FFFFFF; border:1px solid #E5E6EF; border-radius:10px; padding:11px 12px; }}
.brd-metric-icon {{ position:absolute; right:10px; top:9px; width:24px; height:24px; border-radius:6px; display:flex; align-items:center; justify-content:center; color:{PURPLE}; background:#F2EEFF; font-weight:800; font-size:.78rem; }}
.brd-metric-label {{ color:#777A91; font-size:.66rem; font-weight:800; letter-spacing:.035em; padding-right:26px; }}
.brd-metric-value {{ color:{DARK}; font-size:1.32rem; font-weight:900; line-height:1.1; margin-top:9px; }}
.brd-metric-sub {{ color:#7D8092; font-size:.71rem; margin-top:5px; }}
.brd-prediction-card {{ background:#FCFCFF; border:1px solid #E8E8F1; border-radius:10px; padding:12px 13px; margin:.7rem 0; }}
.brd-prediction-label {{ color:#6F7287; font-size:.66rem; font-weight:850; letter-spacing:.035em; }}
.brd-prediction-value {{ color:{DARK}; font-size:1.16rem; font-weight:900; margin-top:4px; }}
.brd-prediction-sub {{ color:#7C7F92; font-size:.72rem; margin-top:2px; }}
.brd-empty {{ font-size:.92rem; }}
.brd-section-title {{ color:{DARK}; font-size:.78rem; font-weight:900; letter-spacing:.025em; }}
.brd-context {{ color:#828497; font-size:.69rem; margin:.08rem 0 .55rem; }}
.brd-target-cell {{ min-height:70px; border-right:1px solid #ECECF3; padding:5px 8px; }}
.brd-target-label {{ color:#838597; font-size:.61rem; font-weight:800; letter-spacing:.035em; }}
.brd-target-value {{ color:{DARK}; font-size:1rem; font-weight:900; margin-top:7px; word-break:break-word; }}
.brd-target-footer {{ display:flex; align-items:center; justify-content:space-between; gap:10px; color:#7E8092; font-size:.69rem; margin-top:3px; flex-wrap:wrap; }}
.brd-subsection-title {{ color:{DARK}; font-size:.7rem; font-weight:900; letter-spacing:.035em; margin-bottom:.35rem; }}
.brd-priority-row {{ padding:6px 0; border-bottom:1px solid #EEEFF4; }}
.brd-priority-topic {{ color:{DARK}; font-size:.78rem; font-weight:850; }}
.brd-priority-subtopic {{ color:#7A7D90; font-size:.7rem; margin-top:2px; }}
.brd-priority-score {{ text-align:right; color:{DARK}; font-size:.78rem; font-weight:850; padding-top:5px; }}
.brd-narrative {{ min-height:115px; border:1px solid #E7E7F0; border-radius:10px; padding:11px 12px; background:#FBFBFE; }}
.brd-insight,.brd-recommendation {{ border-left:3px solid {PURPLE}; }}
.brd-narrative-title {{ color:{PURPLE}; font-size:.65rem; font-weight:900; letter-spacing:.035em; }}
.brd-narrative-text {{ color:#404158; font-size:.77rem; line-height:1.45; margin-top:7px; }}
.tag {{ display:inline-block; border-radius:999px; padding:3px 8px; font-size:.64rem; font-weight:850; }}
.tag-purple {{ background:#EEE9FF; color:{PURPLE}; }} .tag-green {{ background:#E8F8F1; color:#08764A; }}
.tag-orange {{ background:#FFF4E5; color:#A75B00; }} .tag-red {{ background:#FCE9ED; color:#B32B43; }}
.dialog-available,.target-preview {{ display:flex; justify-content:space-between; align-items:center; background:#F5F2FF; border:1px solid #E3DCFF; border-radius:9px; padding:10px 12px; margin:.4rem 0 .65rem; color:{DARK}; }}
.oneview-footer {{ color:#8B8DA1; font-size:.69rem; text-align:center; padding:15px 0 0; }}
button[kind="primary"] {{ background:{PURPLE} !important; border-color:{PURPLE} !important; }}
.stProgress > div > div > div > div {{ background-color:{PURPLE}; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:#E4E5EE !important; border-radius:9px !important; background:white; box-shadow:none !important; }}
[data-testid="stPlotlyChart"] {{ border-radius:8px; overflow:hidden; }}
[data-testid="stMetric"] {{ background:transparent; border:0; padding:0; }}

@media (max-width:1100px) {{
  [data-testid="stSidebar"] {{ min-width:172px !important; max-width:172px !important; width:172px !important; }}
  [data-testid="stSidebar"] > div:first-child {{ width:172px !important; }}
  .block-container {{ padding-left:.85rem; padding-right:.85rem; }}
  .brd-metric-value {{ font-size:1.08rem; }}
}}
</style>
""",
    unsafe_allow_html=True,
)

SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
SUPABASE_ANON_KEY = st.secrets.get("SUPABASE_ANON_KEY", os.getenv("SUPABASE_ANON_KEY"))
if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error("Configure SUPABASE_URL and SUPABASE_ANON_KEY in Streamlit secrets.")
    st.stop()
sb = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)


def current_student():
    access, refresh = st.session_state.get("access_token"), st.session_state.get("refresh_token")
    if not access or not refresh:
        return None
    try:
        res = sb.auth.set_session(access, refresh)
        if res and res.user:
            st.session_state.user = res.user
            if res.session:
                st.session_state.access_token = res.session.access_token
                st.session_state.refresh_token = res.session.refresh_token
            return res.user
    except Exception:
        pass
    for key in ("user", "access_token", "refresh_token"):
        st.session_state.pop(key, None)
    return None


def login():
    st.markdown("<div style='height:10vh'></div>", unsafe_allow_html=True)
    _, center, _ = st.columns([1, 1.25, 1])
    with center:
        with st.container(border=True):
            st.markdown(
                f"<div style='color:{PURPLE};font-weight:900'>◉ ONEVIEW</div>"
                f"<h2 style='color:{DARK};margin:.35rem 0'>Learning Analytics</h2>",
                unsafe_allow_html=True,
            )
            st.caption("Sign in to view your Overview dashboard and record practice papers.")
            email = st.text_input("Email")
            password = st.text_input("Password", type="password")
            if st.button("Sign in", type="primary", use_container_width=True):
                try:
                    res = sb.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user and res.session:
                        st.session_state.user = res.user
                        st.session_state.access_token = res.session.access_token
                        st.session_state.refresh_token = res.session.refresh_token
                        st.session_state.nav = "Overview"
                        st.rerun()
                    st.error("No authenticated session was returned.")
                except Exception as exc:
                    st.error(f"Sign-in failed: {exc}")


def _last_updated(user_id):
    rows = get_df(
        sb,
        "practice_attempts",
        "updated_at,created_at",
        {"student_id": user_id},
        order="updated_at",
        desc=True,
    )
    if rows.empty:
        return "No activity yet"
    stamp = pd.to_datetime(rows.iloc[0].get("updated_at") or rows.iloc[0].get("created_at"), utc=True, errors="coerce")
    return "No activity yet" if pd.isna(stamp) else stamp.strftime("%d %b %Y, %I:%M %p")


def render_global_header(user):
    """Shared BRD header rendered identically on every authenticated MVP page."""
    name = student_name(sb, user)
    st.session_state.setdefault("overview_level", "AS Level")
    current_level = st.session_state.overview_level

    c1, c2, c3, c4 = st.columns([2.7, 2.1, 2.55, 1.85], vertical_alignment="center")
    c1.markdown(f"<div class='brd-student-name'>{name}</div>", unsafe_allow_html=True)
    with c2:
        selected_level = st.segmented_control(
            "Exam Level",
            ["AS Level", "A Level"],
            default=current_level,
            key="global_exam_level",
            label_visibility="collapsed",
        )
        if selected_level and selected_level != st.session_state.overview_level:
            st.session_state.overview_level = selected_level
            st.rerun()
    c3.markdown(
        f"<div class='brd-last-updated'>◷ Last updated: {_last_updated(user.id)}</div>",
        unsafe_allow_html=True,
    )
    if c4.button("+ Record Practice Paper", type="primary", use_container_width=True, key="global_record_action"):
        st.session_state.nav = "Record Practice Paper"
        st.rerun()
    st.divider()


def render_navigation(user):
    pages = [
        ("⌂  Overview", "Overview"),
        ("▣  Record Practice Paper", "Record Practice Paper"),
        ("◔  Topic Analysis", "Topic Analysis"),
    ]
    name = student_name(sb, user)
    with st.sidebar:
        st.markdown("<div class='nav-brand'>◉ ONEVIEW</div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-sub'>Learning Analytics</div>", unsafe_allow_html=True)
        for label, page in pages:
            if st.button(
                label,
                key=f"nav_link_{page}",
                type="primary" if st.session_state.nav == page else "secondary",
                use_container_width=True,
            ):
                if st.session_state.nav != page:
                    st.session_state.nav = page
                    st.rerun()
        st.markdown("<div style='height:33vh'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='nav-user'>{name}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='nav-email'>{user.email or ''}</div>", unsafe_allow_html=True)
        st.markdown("<div style='height:.45rem'></div>", unsafe_allow_html=True)
        if st.button("↪  Log out", key="nav_logout", use_container_width=True):
            try:
                sb.auth.sign_out()
            except Exception:
                pass
            for key in ("user", "access_token", "refresh_token", "nav"):
                st.session_state.pop(key, None)
            st.rerun()


def app():
    user = current_student()
    if not user:
        login()
        return

    pages = ["Overview", "Record Practice Paper", "Topic Analysis"]
    st.session_state.setdefault("nav", "Overview")
    if st.session_state.nav not in pages:
        st.session_state.nav = "Overview"

    render_navigation(user)
    render_global_header(user)

    if st.session_state.nav == "Overview":
        render_overview(sb, user)
    elif st.session_state.nav == "Record Practice Paper":
        render_record_practice(sb, user)
    else:
        render_topic_analysis(sb, user)


app()
