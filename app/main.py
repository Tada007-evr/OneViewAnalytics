import os

import pandas as pd
import streamlit as st
from supabase import create_client

from oneview_db import get_df, student_name
from overview_page_brd import render_overview
from record_page import render_record_practice
from topic_page import render_topic_analysis

st.set_page_config(
    page_title="OneView Learning Analytics",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

PURPLE = "#5A32D5"
DARK = "#17163A"
MUTED = "#7B7D91"
BORDER = "#E8E8F0"

st.markdown(
    f"""
<style>
:root{{--ov-purple:{PURPLE};--ov-dark:{DARK};--ov-muted:{MUTED};}}
html,body,[class*="css"]{{font-family:Inter,Arial,sans-serif;}}
.stApp{{background:#F7F8FC;color:#20213A;}}
.block-container{{max-width:1310px;padding:.35rem 1rem 1.25rem;}}
header[data-testid="stHeader"]{{display:none!important;visibility:hidden!important;height:0!important;pointer-events:none!important;}}
[data-testid="stToolbar"],
[data-testid="stAppDeployButton"],
[data-testid="stMainMenu"],
[data-testid="stStatusWidget"],
[data-testid="stDecoration"],
.stAppToolbar,
#MainMenu{{display:none!important;visibility:hidden!important;pointer-events:none!important;}}

/* BRD LEFT NAVIGATION — matched to the finalized prototype. */
[data-testid="stSidebar"]{{
  background:linear-gradient(180deg,#19145B 0%,#25128D 55%,#2420B6 100%);
  border-right:0;
  min-width:204px!important;max-width:204px!important;width:204px!important;
}}
[data-testid="stSidebar"]>div:first-child{{width:204px!important;padding:0!important;}}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{{padding:0 10px 12px!important;}}
[data-testid="stSidebar"] *{{color:white;}}

.nav-brand-wrap{{height:94px;display:flex;align-items:center;padding:0 10px;margin:0 -10px 20px;border-bottom:0;}}
.nav-logo-svg{{width:42px;height:42px;flex:0 0 auto;margin-right:8px;}}
.nav-brand{{font-size:1.05rem;font-weight:800;letter-spacing:0;color:#fff;line-height:1;}}

[data-testid="stSidebar"] .stButton{{margin:0 0 7px!important;}}
[data-testid="stSidebar"] .stButton>button{{
  width:100%;min-height:76px;height:76px;border:0!important;border-radius:8px!important;box-shadow:none!important;
  justify-content:flex-start!important;text-align:left!important;font-size:.83rem!important;font-weight:600!important;
  padding:0 14px!important;margin:0!important;color:#fff!important;background:transparent!important;line-height:1.35!important;
  gap:13px!important;
}}
[data-testid="stSidebar"] .stButton>button p{{margin:0!important;white-space:normal!important;text-align:left!important;color:#fff!important;line-height:1.35!important;}}
[data-testid="stSidebar"] .stButton>button:hover{{background:rgba(255,255,255,.08)!important;color:#fff!important;}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:linear-gradient(90deg,#5D32E2 0%,#5530D8 100%)!important;color:#fff!important;box-shadow:none!important;}}

/* Prototype line icons: home, record/clipboard, topic/pie. */
.st-key-nav_overview button::before,
.st-key-nav_record button::before,
.st-key-nav_topic button::before,
.st-key-nav_logout button::before{{content:"";display:block;flex:0 0 auto;width:27px;height:27px;background:#fff;}}
.st-key-nav_overview button::before{{
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 10.8 12 3l9 7.8'/%3E%3Cpath d='M5.5 9.4V21h13V9.4'/%3E%3Cpath d='M9.5 21v-7h5v7'/%3E%3C/svg%3E") center/contain no-repeat;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M3 10.8 12 3l9 7.8'/%3E%3Cpath d='M5.5 9.4V21h13V9.4'/%3E%3Cpath d='M9.5 21v-7h5v7'/%3E%3C/svg%3E") center/contain no-repeat;
}}
.st-key-nav_record button::before{{
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='5' y='4.5' width='14' height='16.5' rx='1.8'/%3E%3Cpath d='M9 3h6v3H9z'/%3E%3Cpath d='M8.5 10h7M8.5 14h4M8.5 18h7'/%3E%3C/svg%3E") center/contain no-repeat;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Crect x='5' y='4.5' width='14' height='16.5' rx='1.8'/%3E%3Cpath d='M9 3h6v3H9z'/%3E%3Cpath d='M8.5 10h7M8.5 14h4M8.5 18h7'/%3E%3C/svg%3E") center/contain no-repeat;
}}
.st-key-nav_topic button::before{{
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M11 2.5a9.5 9.5 0 1 0 9.5 9.5H11z'/%3E%3Cpath d='M14 2.8v6.2h6.2A8.1 8.1 0 0 0 14 2.8z'/%3E%3C/svg%3E") center/contain no-repeat;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M11 2.5a9.5 9.5 0 1 0 9.5 9.5H11z'/%3E%3Cpath d='M14 2.8v6.2h6.2A8.1 8.1 0 0 0 14 2.8z'/%3E%3C/svg%3E") center/contain no-repeat;
}}

.nav-spacer{{height:39vh;min-height:245px;max-height:430px;}}
.nav-user-block{{padding:0 8px 17px;border:0;}}
.nav-avatar-row{{display:flex;align-items:center;gap:9px;}}
.nav-avatar{{width:35px;height:35px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#5B35E8;color:#fff;font-size:.68rem;font-weight:700;flex:0 0 auto;}}
.nav-user-meta{{min-width:0;display:flex;flex-direction:column;justify-content:center;}}
.nav-switch{{font-size:.62rem;color:#fff;line-height:1.15;margin-bottom:5px;}}
.nav-user{{font-size:.66rem;font-weight:500;color:#fff;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.nav-user-chevron{{font-size:.55rem;color:#D8D3FF;margin-left:4px;vertical-align:1px;}}

.nav-logout-wrap{{border-top:1px solid rgba(255,255,255,.12);padding:9px 0 0;margin:0 -2px;}}
[data-testid="stSidebar"] .st-key-nav_logout{{margin:0!important;}}
[data-testid="stSidebar"] .st-key-nav_logout button{{
  min-height:58px!important;height:58px!important;padding:0 14px!important;font-size:.72rem!important;font-weight:500!important;
  background:transparent!important;box-shadow:none!important;border:0!important;color:#fff!important;justify-content:flex-start!important;text-align:left!important;gap:13px!important;
}}
[data-testid="stSidebar"] .st-key-nav_logout button p{{font-size:.72rem!important;color:#fff!important;white-space:nowrap!important;line-height:1!important;}}
.st-key-nav_logout button::before{{
  width:25px;height:25px;
  -webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 4H4v16h6'/%3E%3Cpath d='M13 8l4 4-4 4'/%3E%3Cpath d='M8 12h9'/%3E%3C/svg%3E") center/contain no-repeat;
  mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 4H4v16h6'/%3E%3Cpath d='M13 8l4 4-4 4'/%3E%3Cpath d='M8 12h9'/%3E%3C/svg%3E") center/contain no-repeat;
}}
[data-testid="stSidebar"] .st-key-nav_logout button:hover{{background:rgba(255,255,255,.06)!important;}}

/* GLOBAL HEADER */
.global-student{{font-size:.92rem;font-weight:900;color:{DARK};padding-top:.36rem;white-space:nowrap;}}
.global-label{{font-size:.52rem;color:#8B8D9F;font-weight:750;margin-bottom:.12rem;text-align:right;}}
.global-updated{{font-size:.56rem;color:#888A9B;text-align:right;white-space:nowrap;padding-top:.42rem;}}
[data-testid="stSegmentedControl"] button{{font-size:.57rem!important;min-height:28px!important;padding:.13rem .5rem!important;border-radius:4px!important;}}
[data-testid="stSegmentedControl"] [aria-pressed="true"]{{background:{PURPLE}!important;color:white!important;}}
.st-key-global_action_wrap{{padding-top:.34rem!important;position:relative!important;z-index:20!important;pointer-events:auto!important;}}
.st-key-global_action_wrap .stButton,.st-key-global_action_wrap .stButton>button{{position:relative!important;z-index:21!important;pointer-events:auto!important;}}
.st-key-global_action_wrap .stButton>button{{font-size:.57rem!important;min-height:30px!important;padding:.2rem .55rem!important;}}

/* SHARED BRD VISUAL SYSTEM */
.brd-page-label{{display:none;}}
div[data-testid="stVerticalBlockBorderWrapper"]{{border-color:{BORDER}!important;border-radius:7px!important;background:#fff;box-shadow:0 1px 3px rgba(28,25,64,.035)!important;}}
.brd-subject-title{{font-size:.76rem;font-weight:900;color:{DARK};display:flex;align-items:center;gap:6px;letter-spacing:.015em;}}
.subject-icon{{width:25px;height:25px;display:inline-flex;align-items:center;justify-content:center;border-radius:5px;background:#5B35D5;color:white;font-weight:900;font-size:.62rem;}}
.brd-subject-meta{{color:#777A90;font-size:.56rem;margin:.22rem 0 .5rem;}}
.brd-metric-card{{position:relative;min-height:84px;background:#fff;border:1px solid #ECECF3;border-radius:6px;padding:8px 9px;}}
.brd-metric-icon{{position:absolute;right:7px;top:7px;width:20px;height:20px;border-radius:5px;display:flex;align-items:center;justify-content:center;color:{PURPLE};background:#F0ECFF;font-weight:800;font-size:.62rem;}}
.brd-metric-label{{color:#7B7D91;font-size:.49rem;font-weight:850;letter-spacing:.025em;padding-right:20px;}}
.brd-metric-value{{color:{DARK};font-size:1.04rem;font-weight:900;line-height:1.08;margin-top:7px;}}
.brd-metric-sub{{color:#777A8D;font-size:.54rem;margin-top:3px;}}
.brd-prediction-card{{background:#fff;border:1px solid #ECECF3;border-radius:6px;padding:8px 10px;margin:.5rem 0;}}
.brd-prediction-label{{color:#6E7187;font-size:.5rem;font-weight:850;letter-spacing:.025em;}}
.brd-prediction-value{{color:{DARK};font-size:.94rem;font-weight:900;margin-top:3px;}}
.brd-prediction-sub{{color:#7E8093;font-size:.54rem;margin-top:1px;}}
.brd-subsection-title{{color:#6F7185;font-size:.51rem;font-weight:900;letter-spacing:.035em;margin-bottom:.25rem;}}
.brd-priority-row{{padding:4px 0;border-bottom:1px solid #F0F0F5;}}
.brd-priority-topic{{color:{DARK};font-size:.61rem;font-weight:850;}}
.brd-priority-subtopic{{color:#808295;font-size:.54rem;margin-top:1px;}}
.brd-priority-score{{text-align:right;color:{DARK};font-size:.61rem;font-weight:850;padding-top:3px;}}
.brd-narrative{{min-height:92px;border:1px solid #ECECF3;border-radius:6px;padding:8px 9px;background:#FBFAFF;border-left:2px solid {PURPLE};}}
.brd-narrative-title{{color:{PURPLE};font-size:.49rem;font-weight:900;letter-spacing:.03em;}}
.brd-narrative-text{{color:#404158;font-size:.58rem;line-height:1.38;margin-top:5px;}}
.tag{{display:inline-block;border-radius:999px;padding:2px 6px;font-size:.48rem;font-weight:850;}}
.tag-purple{{background:#EEE9FF;color:{PURPLE};}}.tag-green{{background:#E8F8F1;color:#08764A;}}.tag-orange{{background:#FFF4E5;color:#A75B00;}}.tag-red{{background:#FCE9ED;color:#B32B43;}}
.brd-section-title{{color:{DARK};font-size:.62rem;font-weight:900;letter-spacing:.02em;}}
.brd-context{{color:#828497;font-size:.53rem;margin:.05rem 0 .35rem;}}
.brd-target-cell{{min-height:58px;border-right:1px solid #ECECF3;padding:4px 6px;}}
.brd-target-label{{color:#838597;font-size:.47rem;font-weight:800;letter-spacing:.03em;}}
.brd-target-value{{color:{DARK};font-size:.78rem;font-weight:900;margin-top:5px;}}
.brd-target-footer{{display:flex;align-items:center;justify-content:space-between;gap:7px;color:#7E8092;font-size:.52rem;margin-top:2px;flex-wrap:wrap;}}
.oneview-footer{{color:#9092A2;font-size:.52rem;text-align:center;padding:9px 0 0;}}
.dialog-available,.target-preview{{display:flex;justify-content:space-between;align-items:center;background:#F5F2FF;border:1px solid #E3DCFF;border-radius:7px;padding:8px 10px;margin:.35rem 0 .55rem;color:{DARK};}}
button[kind="primary"]{{background:{PURPLE}!important;border-color:{PURPLE}!important;}}
.stProgress>div>div>div>div{{background-color:{PURPLE};}}
[data-testid="stPlotlyChart"]{{border-radius:5px;overflow:hidden;}}
.stButton>button{{border-radius:5px;font-size:.61rem;min-height:31px;}}
.stSelectbox label,.stDateInput label,.stTextInput label,.stNumberInput label{{font-size:.57rem!important;font-weight:750!important;color:#34334F!important;}}
[data-baseweb="select"]>div,input{{font-size:.61rem!important;}}
hr{{margin:.25rem 0 .55rem!important;}}

@media(max-width:1100px){{
 [data-testid="stSidebar"]{{min-width:194px!important;max-width:194px!important;width:194px!important;}}
 [data-testid="stSidebar"]>div:first-child{{width:194px!important;}}
 .nav-spacer{{height:24vh;min-height:135px;max-height:255px;}}
 .block-container{{padding-left:.75rem;padding-right:.75rem;}}
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
    access = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")
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
    _, center, _ = st.columns([1, 1.15, 1])
    with center:
        with st.container(border=True):
            st.markdown(
                f"<div style='color:{PURPLE};font-weight:900'>◉ ONEVIEW</div>"
                f"<h2 style='color:{DARK};margin:.35rem 0'>Learning Analytics</h2>",
                unsafe_allow_html=True,
            )
            st.caption("Sign in to view your OneView learning analytics.")
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
    rows = get_df(sb, "practice_attempts", "updated_at,created_at", {"student_id": user_id}, order="updated_at", desc=True)
    if rows.empty:
        return "No activity yet"
    stamp = pd.to_datetime(rows.iloc[0].get("updated_at") or rows.iloc[0].get("created_at"), utc=True, errors="coerce")
    return "No activity yet" if pd.isna(stamp) else stamp.strftime("%d %b %Y, %I:%M %p")


def _go_to(page):
    st.session_state.nav = page


def render_global_header(user):
    name = student_name(sb, user)
    st.session_state.setdefault("overview_level", "AS Level")
    current = st.session_state.overview_level
    if st.session_state.get("global_exam_level") != current:
        st.session_state.global_exam_level = current

    c1, c2, c3, c4 = st.columns([2.6, 2.45, 3.0, 1.75], vertical_alignment="center", gap="small")
    c1.markdown(f"<div class='global-student'>{name}</div>", unsafe_allow_html=True)
    with c2:
        label, control = st.columns([.75, 2.1], vertical_alignment="center", gap="small")
        label.markdown("<div class='global-label'>Exam Level</div>", unsafe_allow_html=True)
        with control:
            selected = st.segmented_control("Exam Level", ["AS Level", "A Level"], key="global_exam_level", label_visibility="collapsed")
            if selected and selected != st.session_state.overview_level:
                st.session_state.overview_level = selected
                st.rerun()
    c3.markdown(f"<div class='global-updated'>◷&nbsp; Last updated: {_last_updated(user.id)}</div>", unsafe_allow_html=True)
    with c4:
        with st.container(key="global_action_wrap"):
            st.button(
                "+ Record Practice Paper",
                type="primary",
                use_container_width=True,
                key="global_record_action",
                on_click=_go_to,
                args=("Record Practice Paper",),
            )
    st.divider()


def render_navigation(user):
    pages = [
        ("Overview", "Overview", "nav_overview"),
        ("Record\nPractice Paper", "Record Practice Paper", "nav_record"),
        ("Topic Analysis", "Topic Analysis", "nav_topic"),
    ]
    name = student_name(sb, user)
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "LE"

    with st.sidebar:
        st.markdown(
            """
            <div class='nav-brand-wrap'>
              <svg class='nav-logo-svg' viewBox='0 0 48 48' fill='none' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'>
                <circle cx='24' cy='24' r='20.5' stroke='white' stroke-width='1.7'/>
                <path d='M14 31V26M20 31V22M26 31V18M32 31V14' stroke='white' stroke-width='1.8' stroke-linecap='round'/>
                <path d='M13 21.5L19 18L24.5 20.5L33 12' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/>
                <path d='M29.5 12H33V15.5' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/>
              </svg>
              <span class='nav-brand'>ONEVIEW</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for label, page, key in pages:
            st.button(
                label,
                key=key,
                type="primary" if st.session_state.nav == page else "secondary",
                use_container_width=True,
                on_click=_go_to,
                args=(page,),
            )

        st.markdown("<div class='nav-spacer'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='nav-user-block'><div class='nav-avatar-row'>"
            f"<div class='nav-avatar'>{initials}</div>"
            f"<div class='nav-user-meta'><div class='nav-switch'>Switch Student</div>"
            f"<div class='nav-user'>{name}<span class='nav-user-chevron'>⌄</span></div>"
            f"</div></div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='nav-logout-wrap'>", unsafe_allow_html=True)
        if st.button("Logout", key="nav_logout", use_container_width=True):
            try:
                sb.auth.sign_out()
            except Exception:
                pass
            for key in ("user", "access_token", "refresh_token", "nav"):
                st.session_state.pop(key, None)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


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

    page = st.session_state.nav
    if page == "Overview":
        render_overview(sb, user)
    elif page == "Record Practice Paper":
        render_record_practice(sb, user)
    else:
        render_topic_analysis(sb, user)


app()
