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
:root {{ --ov-purple:{PURPLE}; --ov-dark:{DARK}; --ov-muted:{MUTED}; }}
.stApp {{background:linear-gradient(180deg,#F8F9FD 0%,#F5F6FA 100%);color:#20213A;}}
[data-testid="stSidebar"] {{background:linear-gradient(180deg,#3514A0 0%,#27107D 100%);box-shadow:6px 0 24px rgba(36,18,112,.12);}}
[data-testid="stSidebar"] * {{color:white;}}
[data-testid="stSidebar"] [data-baseweb="radio"] label {{border-radius:10px;padding:10px 12px;margin:3px 0;transition:.18s ease;}}
[data-testid="stSidebar"] [data-baseweb="radio"] label:hover {{background:rgba(255,255,255,.09);}}
[data-testid="stSidebar"] [data-baseweb="radio"] label:has(input:checked) {{background:rgba(255,255,255,.17);box-shadow:inset 3px 0 0 rgba(255,255,255,.9);}}
.block-container {{padding-top:1.25rem;max-width:1500px;padding-bottom:2rem;}}
.ov-title {{font-size:1.36rem;font-weight:850;color:{DARK};line-height:1.2;}}
.ov-kicker {{color:{PURPLE};font-weight:850;font-size:.78rem;letter-spacing:.075em;}}
.ov-muted {{color:{MUTED};font-size:.82rem;}}
.subject-title {{font-size:1rem;font-weight:900;color:{DARK};margin-bottom:2px;letter-spacing:.015em;}}
.subject-icon {{display:inline-flex;width:28px;height:28px;align-items:center;justify-content:center;border-radius:9px;background:#EEE9FF;color:{PURPLE};font-weight:900;margin-right:6px;}}
.level-pill {{display:inline-block;float:right;padding:5px 9px;border-radius:999px;background:#F2F0FB;color:{PURPLE};font-size:.7rem;font-weight:800;}}
.metric-card {{position:relative;border:1px solid #E8E8F1;border-radius:14px;background:linear-gradient(180deg,#FFFFFF 0%,#FCFCFF 100%);padding:13px 14px;min-height:112px;box-shadow:0 5px 18px rgba(43,33,85,.055);transition:transform .15s ease,box-shadow .15s ease;overflow:hidden;}}
.metric-card:hover {{transform:translateY(-1px);box-shadow:0 8px 24px rgba(43,33,85,.085);}}
.metric-card:after {{content:"";position:absolute;left:0;top:0;width:3px;height:100%;background:linear-gradient(180deg,{PURPLE},#9278EC);}}
.metric-icon {{position:absolute;right:12px;top:10px;width:26px;height:26px;border-radius:8px;background:#F0ECFF;color:{PURPLE};display:flex;align-items:center;justify-content:center;font-weight:900;}}
.metric-label {{color:#73758A;font-size:.69rem;font-weight:800;text-transform:uppercase;letter-spacing:.055em;}}
.metric-value {{color:{DARK};font-size:1.4rem;font-weight:900;margin-top:7px;line-height:1.15;}}
.metric-sub {{color:#777A91;font-size:.75rem;margin-top:5px;}}
.tag {{display:inline-block;border-radius:999px;padding:4px 9px;font-size:.7rem;font-weight:850;}}
.tag-purple {{background:#EEE9FF;color:{PURPLE};}}
.tag-green {{background:#E8F8F1;color:#08764A;}}
.tag-orange {{background:#FFF4E5;color:#A75B00;}}
.tag-red {{background:#FCE9ED;color:#B32B43;}}
div[data-testid="stVerticalBlockBorderWrapper"] {{border-color:#E6E6EF !important;border-radius:16px !important;background:white;box-shadow:0 7px 25px rgba(43,33,85,.045);}}
.oneview-footer {{color:#8B8DA1;font-size:.72rem;text-align:center;padding:18px 0 2px;}}
.priority-row {{padding:7px 0 4px;border-bottom:1px solid #F0EFF5;}}
.priority-title {{font-size:.82rem;font-weight:800;color:{DARK};}}
.priority-sub {{font-size:.74rem;color:#777A91;margin-top:1px;}}
button[kind="primary"] {{background:linear-gradient(135deg,{PURPLE},#7556E0) !important;border-color:{PURPLE} !important;box-shadow:0 5px 14px rgba(91,53,213,.22);}}
button[kind="primary"]:hover {{filter:brightness(.98);transform:translateY(-1px);}}
.stProgress > div > div > div > div {{background-color:{PURPLE};}}
.section-rule {{height:1px;background:linear-gradient(90deg,transparent,#E2E1EA,transparent);margin:.55rem 0 1rem;}}
.dialog-available {{background:#F5F2FF;border:1px solid #E5DFFF;border-radius:12px;padding:10px 12px;margin:.4rem 0 .6rem;color:{DARK};display:flex;justify-content:space-between;}}
.narrative-card {{border-radius:13px;padding:13px 14px;min-height:116px;border:1px solid #E8E8F1;background:#FCFCFF;}}
.narrative-insight {{border-left:4px solid {PURPLE};}}
.narrative-rec {{border-left:4px solid #18A66A;}}
.narrative-kicker {{font-size:.68rem;font-weight:900;letter-spacing:.06em;color:{PURPLE};margin-bottom:5px;}}
[data-testid="stMetric"] {{background:#FCFCFF;border:1px solid #ECEBF3;padding:8px 10px;border-radius:12px;}}
[data-testid="stPlotlyChart"] {{border-radius:12px;overflow:hidden;}}
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
