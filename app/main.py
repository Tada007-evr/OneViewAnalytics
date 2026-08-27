import os
import streamlit as st
from supabase import create_client
from oneview_db import student_name
from overview_page import render_overview
from record_page import render_record_practice
from topic_page import render_topic_analysis

st.set_page_config(page_title="OneView Learning Analytics", page_icon="◉", layout="wide", initial_sidebar_state="expanded")

PURPLE = "#5B35D5"
DARK = "#211A4A"
MUTED = "#777A91"

st.markdown(f"""
<style>
:root {{ --ov-purple:{PURPLE}; --ov-dark:{DARK}; --ov-muted:{MUTED}; }}
.stApp {{ background:#F7F8FC; color:#20213A; }}
.block-container {{ max-width:1480px; padding-top:1.1rem; padding-bottom:1.6rem; }}

[data-testid="stSidebar"] {{ background:#31128F; border-right:0; }}
[data-testid="stSidebar"] * {{ color:white; }}
[data-testid="stSidebar"] [data-baseweb="radio"] label {{ border-radius:7px; padding:10px 11px; margin:2px 0; }}
[data-testid="stSidebar"] [data-baseweb="radio"] label:has(input:checked) {{ background:#5633C8; }}

.brd-student-name {{ font-size:1.1rem; font-weight:800; color:{DARK}; padding-top:.25rem; }}
.brd-last-updated {{ text-align:right; color:{MUTED}; font-size:.76rem; padding:.2rem 0 .38rem; }}
.brd-page-label {{ color:{PURPLE}; font-size:.75rem; font-weight:900; letter-spacing:.06em; margin:.55rem 0 .7rem; }}

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
.brd-insight {{ border-left:3px solid {PURPLE}; }}
.brd-recommendation {{ border-left:3px solid #5B35D5; }}
.brd-narrative-title {{ color:{PURPLE}; font-size:.65rem; font-weight:900; letter-spacing:.035em; }}
.brd-narrative-text {{ color:#404158; font-size:.77rem; line-height:1.45; margin-top:7px; }}
.brd-rule {{ color:#9294A3; font-size:.62rem; margin-top:6px; }}

.tag {{ display:inline-block; border-radius:999px; padding:3px 8px; font-size:.64rem; font-weight:850; }}
.tag-purple {{ background:#EEE9FF; color:{PURPLE}; }}
.tag-green {{ background:#E8F8F1; color:#08764A; }}
.tag-orange {{ background:#FFF4E5; color:#A75B00; }}
.tag-red {{ background:#FCE9ED; color:#B32B43; }}

.dialog-available, .target-preview {{ display:flex; justify-content:space-between; align-items:center; background:#F5F2FF; border:1px solid #E3DCFF; border-radius:9px; padding:10px 12px; margin:.4rem 0 .65rem; color:{DARK}; }}
.oneview-footer {{ color:#8B8DA1; font-size:.69rem; text-align:center; padding:15px 0 0; }}

button[kind="primary"] {{ background:{PURPLE} !important; border-color:{PURPLE} !important; }}
.stProgress > div > div > div > div {{ background-color:{PURPLE}; }}
div[data-testid="stVerticalBlockBorderWrapper"] {{ border-color:#E4E5EE !important; border-radius:11px !important; background:white; box-shadow:none !important; }}
[data-testid="stPlotlyChart"] {{ border-radius:8px; overflow:hidden; }}
[data-testid="stMetric"] {{ background:transparent; border:0; padding:0; }}

@media (max-width: 1100px) {{
  .block-container {{ padding-left:1rem; padding-right:1rem; }}
  .brd-metric-value {{ font-size:1.08rem; }}
}}
</style>
""", unsafe_allow_html=True)

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
            st.markdown(f"<div style='color:{PURPLE};font-weight:900'>◉ ONEVIEW</div><h2 style='color:{DARK};margin:.35rem 0'>Learning Analytics</h2>", unsafe_allow_html=True)
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


def app():
    user = current_student()
    if not user:
        login()
        return

    pages = ["Overview", "Record Practice Paper", "Topic Analysis"]
    st.session_state.setdefault("nav", "Overview")
    if st.session_state.nav not in pages:
        st.session_state.nav = "Overview"
    name = student_name(sb, user)

    with st.sidebar:
        st.markdown("### ◉ ONEVIEW")
        st.caption("Learning Analytics")
        selected = st.radio("Navigation", pages, index=pages.index(st.session_state.nav))
        if selected != st.session_state.nav:
            st.session_state.nav = selected
            st.rerun()
        st.markdown("<div style='height:28vh'></div>", unsafe_allow_html=True)
        st.write(f"**{name}**")
        st.caption(user.email or "")
        if st.button("Log out", use_container_width=True):
            try:
                sb.auth.sign_out()
            except Exception:
                pass
            for key in ("user", "access_token", "refresh_token", "nav"):
                st.session_state.pop(key, None)
            st.rerun()

    if st.session_state.nav == "Overview":
        render_overview(sb, user)
    elif st.session_state.nav == "Record Practice Paper":
        render_record_practice(sb, user)
    else:
        render_topic_analysis(sb, user)


app()
