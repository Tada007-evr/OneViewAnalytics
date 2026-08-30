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

/* BRD LEFT NAVIGATION */
[data-testid="stSidebar"]{{
  background:linear-gradient(180deg,#25106D 0%,#2B147E 48%,#21106B 100%);
  border-right:0;
  min-width:174px!important;max-width:174px!important;width:174px!important;
}}
[data-testid="stSidebar"]>div:first-child{{width:174px!important;padding:0!important;}}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{{padding:.72rem .65rem .8rem!important;}}
[data-testid="stSidebar"] *{{color:white;}}
.nav-brand-wrap{{height:57px;display:flex;align-items:center;border-bottom:1px solid rgba(255,255,255,.08);margin:-.1rem -.65rem .72rem;padding:0 .75rem;}}
.nav-logo{{width:23px;height:23px;border-radius:50%;border:1.5px solid #CFC9FF;display:inline-flex;align-items:center;justify-content:center;margin-right:7px;font-size:.72rem;}}
.nav-brand{{font-size:.78rem;font-weight:900;letter-spacing:.035em;}}
.nav-stack{{display:flex;flex-direction:column;gap:4px;}}
[data-testid="stSidebar"] .stButton{{margin:0!important;}}
[data-testid="stSidebar"] .stButton>button{{
  width:100%;height:43px;min-height:43px;border:0;border-radius:7px;box-shadow:none;
  justify-content:flex-start;text-align:left;font-size:.67rem;font-weight:650;
  padding:0 .58rem;margin:0;color:#F5F3FF;background:transparent;line-height:1.1;
}}
[data-testid="stSidebar"] .stButton>button p{{margin:0!important;white-space:normal;text-align:left;}}
[data-testid="stSidebar"] .stButton>button:hover{{background:#38208C;color:white;border:0;}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:#5B35D5!important;color:white!important;border:0!important;box-shadow:0 4px 12px rgba(91,53,213,.28)!important;}}
.nav-spacer{{height:15vh;min-height:70px;max-height:125px;}}
.nav-user-block{{border-top:1px solid rgba(255,255,255,.10);padding:.65rem .18rem .28rem;}}
.nav-avatar-row{{display:flex;align-items:center;gap:8px;}}
.nav-avatar{{width:26px;height:26px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#684BE1;color:#fff;font-size:.56rem;font-weight:900;flex:0 0 auto;}}
.nav-user-meta{{min-width:0;}}
.nav-user{{font-size:.72rem;font-weight:850;color:white;line-height:1.2;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.nav-level{{font-size:.53rem;color:#CBC6EB;margin-top:.18rem;}}
.nav-logout-wrap{{border-top:1px solid rgba(255,255,255,.08);padding-top:.35rem;margin-top:.12rem;}}

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
 [data-testid="stSidebar"]{{min-width:164px!important;max-width:164px!important;width:164px!important;}}
 [data-testid="stSidebar"]>div:first-child{{width:164px!important;}}
 .nav-spacer{{height:9vh;min-height:45px;max-height:75px;}}
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
        ("⌂  Overview", "Overview"),
        ("▤  Record Practice Paper", "Record Practice Paper"),
        ("◔  Topic Analysis", "Topic Analysis"),
    ]
    name = student_name(sb, user)
    level = st.session_state.get("overview_level", "AS Level")
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "LE"

    with st.sidebar:
        st.markdown("<div class='nav-brand-wrap'><span class='nav-logo'>◉</span><span class='nav-brand'>ONEVIEW</span></div>", unsafe_allow_html=True)
        st.markdown("<div class='nav-stack'>", unsafe_allow_html=True)
        for label, page in pages:
            st.button(
                label,
                key=f"nav_link_{page}",
                type="primary" if st.session_state.nav == page else "secondary",
                use_container_width=True,
                on_click=_go_to,
                args=(page,),
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div class='nav-spacer'></div>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='nav-user-block'><div class='nav-avatar-row'>"
            f"<div class='nav-avatar'>{initials}</div>"
            f"<div class='nav-user-meta'><div class='nav-user'>{name}</div>"
            f"<div class='nav-level'>{level}</div></div></div></div>",
            unsafe_allow_html=True,
        )
        st.markdown("<div class='nav-logout-wrap'>", unsafe_allow_html=True)
        if st.button("↪  Log Out", key="nav_logout", use_container_width=True):
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
