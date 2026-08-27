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
MUTED = "#6B7280"

st.markdown(f"""
<style>
.stApp {{background:#F7F8FC;color:#20213A;}}
[data-testid="stSidebar"] {{background:linear-gradient(180deg,#3514A0 0%,#27107D 100%);}}
[data-testid="stSidebar"] * {{color:white;}}
[data-testid="stSidebar"] [data-baseweb="radio"] label {{border-radius:10px;padding:9px 10px;margin:2px 0;}}
[data-testid="stSidebar"] [data-baseweb="radio"] label:has(input:checked) {{background:rgba(255,255,255,.16);}}
.block-container {{padding-top:1.25rem;max-width:1450px;}}
.ov-title {{font-size:1.25rem;font-weight:800;color:{DARK};}}
.ov-kicker {{color:{PURPLE};font-weight:800;font-size:.83rem;letter-spacing:.02em;}}
.ov-muted {{color:{MUTED};font-size:.84rem;}}
.subject-title {{font-size:1rem;font-weight:900;color:{DARK};margin-bottom:2px;}}
.metric-card {{border:1px solid #E9E8F1;border-radius:12px;background:white;padding:12px 13px;min-height:104px;}}
.metric-label {{color:#73758A;font-size:.72rem;font-weight:750;text-transform:uppercase;letter-spacing:.03em;}}
.metric-value {{color:{DARK};font-size:1.42rem;font-weight:900;margin-top:6px;}}
.metric-sub {{color:#777A91;font-size:.77rem;margin-top:2px;}}
.tag {{display:inline-block;border-radius:999px;padding:3px 8px;font-size:.72rem;font-weight:800;}}
.tag-purple {{background:#EEE9FF;color:{PURPLE};}}
.tag-green {{background:#E8F8F1;color:#08764A;}}
.tag-orange {{background:#FFF4E5;color:#A75B00;}}
.tag-red {{background:#FCE9ED;color:#B32B43;}}
div[data-testid="stVerticalBlockBorderWrapper"] {{border-color:#E7E7F0 !important;border-radius:14px !important;background:white;}}
.oneview-footer {{color:#8B8DA1;font-size:.73rem;text-align:center;padding:16px 0 2px;}}
.priority-row {{padding:8px 0 3px;border-bottom:1px solid #F0EFF5;}}
.priority-title {{font-size:.84rem;font-weight:800;color:{DARK};}}
.priority-sub {{font-size:.76rem;color:#777A91;}}
button[kind="primary"] {{background:{PURPLE} !important;border-color:{PURPLE} !important;}}
.stProgress > div > div > div > div {{background-color:{PURPLE};}}
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
            st.markdown(f"<div class='ov-kicker'>◉ ONEVIEW</div><h2 style='color:{DARK};margin:.35rem 0'>Learning Analytics</h2>", unsafe_allow_html=True)
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
