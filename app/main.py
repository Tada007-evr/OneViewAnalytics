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

PURPLE = "#3A29D9"
BRD_BLUE = "#3526D7"
DARK = "#111044"
MUTED = "#73748A"
BORDER = "#E3E4EE"

st.markdown(
    f"""
<style>
:root{{--ov-purple:{PURPLE};--ov-dark:{DARK};--ov-muted:{MUTED};}}
html,body,[class*="css"]{{font-family:"Arial Narrow",Arial,sans-serif;}}
.stApp{{background:#FFFFFF;color:{DARK};}}
.block-container{{max-width:1310px;padding:.30rem 1rem 1.25rem;}}
header[data-testid="stHeader"]{{display:none!important;visibility:hidden!important;height:0!important;pointer-events:none!important;}}
[data-testid="stToolbar"],[data-testid="stAppDeployButton"],[data-testid="stMainMenu"],[data-testid="stStatusWidget"],[data-testid="stDecoration"],.stAppToolbar,#MainMenu{{display:none!important;visibility:hidden!important;pointer-events:none!important;}}
[data-testid="stSidebarCollapsedControl"]{{display:none!important;visibility:hidden!important;}}

/* Dedicated OneView sidebar arrows: left hides, right restores. */
[data-testid="stSidebar"] .st-key-nav_collapse{{position:absolute!important;top:10px!important;right:8px!important;z-index:100!important;width:28px!important;}}
[data-testid="stSidebar"] .st-key-nav_collapse .stButton{{margin:0!important;}}
[data-testid="stSidebar"] .st-key-nav_collapse button{{width:28px!important;height:28px!important;min-height:28px!important;padding:0!important;border:0!important;border-radius:6px!important;background:rgba(255,255,255,.10)!important;color:#fff!important;font-size:.82rem!important;font-weight:800!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:none!important;}}
[data-testid="stSidebar"] .st-key-nav_collapse button:hover{{background:rgba(255,255,255,.19)!important;}}
.st-key-sidebar_expand_wrap{{position:fixed!important;left:8px!important;top:8px!important;z-index:10000!important;width:34px!important;}}
.st-key-sidebar_expand_wrap .stButton{{margin:0!important;}}
.st-key-sidebar_expand_wrap button{{width:34px!important;height:34px!important;min-height:34px!important;padding:0!important;border:0!important;border-radius:7px!important;background:#1D187E!important;color:#fff!important;font-size:.90rem!important;font-weight:800!important;display:flex!important;align-items:center!important;justify-content:center!important;box-shadow:0 1px 4px rgba(17,16,68,.18)!important;}}
.st-key-sidebar_expand_wrap button:hover{{background:#2821A3!important;}}

/* Finalized BRD shared left navigation */
[data-testid="stSidebar"]{{background:linear-gradient(180deg,#17145B 0%,#1D187E 50%,#2420B6 100%);border-right:0;min-width:204px!important;max-width:204px!important;width:204px!important;}}
[data-testid="stSidebar"]>div:first-child{{width:204px!important;padding:0!important;}}
[data-testid="stSidebar"] [data-testid="stSidebarContent"]{{padding:0 11px 10px!important;overflow-y:auto!important;}}
[data-testid="stSidebar"] *{{color:white;}}
.nav-brand-wrap{{height:82px;display:flex;align-items:center;padding:0 9px;margin:0 -11px 9px;}}
.nav-logo-svg{{width:38px;height:38px;flex:0 0 auto;margin-right:8px;}}
.nav-brand{{font-size:1.02rem;font-weight:700;letter-spacing:.01em;color:#fff;line-height:1;}}
[data-testid="stSidebar"] .stButton{{margin:0 0 5px!important;}}
[data-testid="stSidebar"] .stButton>button{{width:100%;min-height:57px;height:57px;border:0!important;border-radius:8px!important;box-shadow:none!important;justify-content:flex-start!important;text-align:left!important;font-size:.75rem!important;font-weight:600!important;padding:0 13px!important;margin:0!important;color:#fff!important;background:transparent!important;line-height:1.22!important;gap:11px!important;}}
/* Force every navigation text block to the identical x-coordinate after its 23px icon. */
[data-testid="stSidebar"] .st-key-nav_overview button,
[data-testid="stSidebar"] .st-key-nav_record button,
[data-testid="stSidebar"] .st-key-nav_topic button{{display:grid!important;grid-template-columns:23px minmax(0,1fr)!important;column-gap:11px!important;align-items:center!important;}}
[data-testid="stSidebar"] .st-key-nav_overview button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .st-key-nav_record button [data-testid="stMarkdownContainer"],
[data-testid="stSidebar"] .st-key-nav_topic button [data-testid="stMarkdownContainer"]{{grid-column:2!important;margin:0!important;padding:0!important;min-width:0!important;width:100%!important;justify-self:stretch!important;}}
[data-testid="stSidebar"] .st-key-nav_overview button p,
[data-testid="stSidebar"] .st-key-nav_record button p,
[data-testid="stSidebar"] .st-key-nav_topic button p{{margin:0!important;padding:0!important;white-space:pre-line!important;text-align:left!important;color:#fff!important;line-height:1.22!important;}}
[data-testid="stSidebar"] .stButton>button:hover{{background:rgba(255,255,255,.07)!important;color:#fff!important;}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:linear-gradient(90deg,#6841E4 0%,#5E39D9 100%)!important;color:#fff!important;box-shadow:none!important;}}
.st-key-nav_overview button::before,.st-key-nav_record button::before,.st-key-nav_topic button::before,.st-key-nav_logout button::before{{content:"";display:block;flex:0 0 auto;width:23px;height:23px;background:#fff;}}
.st-key-nav_overview button::before,.st-key-nav_record button::before,.st-key-nav_topic button::before{{grid-column:1!important;}}
.st-key-nav_overview button::before{{-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'%3E%3Cpath d='M3 10.7 12 3l9 7.7v10.1H14.7v-6.4H9.3v6.4H3z'/%3E%3C/svg%3E") center/contain no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='black'%3E%3Cpath d='M3 10.7 12 3l9 7.7v10.1H14.7v-6.4H9.3v6.4H3z'/%3E%3C/svg%3E") center/contain no-repeat;}}
.st-key-nav_record button::before{{-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 4h10l4 4v12H5z'/%3E%3Cpath d='M15 4v4h4M9 13h6M9 17h4M7 8h4'/%3E%3C/svg%3E") center/contain no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M5 4h10l4 4v12H5z'/%3E%3Cpath d='M15 4v4h4M9 13h6M9 17h4M7 8h4'/%3E%3C/svg%3E") center/contain no-repeat;}}
.st-key-nav_topic button::before{{-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round'%3E%3Cpath d='M4 20h16M7 17V9M12 17V4M17 17v-6'/%3E%3C/svg%3E") center/contain no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round'%3E%3Cpath d='M4 20h16M7 17V9M12 17V4M17 17v-6'/%3E%3C/svg%3E") center/contain no-repeat;}}
/* Keep student identity and logout visibly above the bottom edge, matching prototype placement. */
.nav-spacer{{height:10vh;min-height:48px;max-height:90px;}}
.nav-user-block{{padding:0 7px 9px;border:0;position:relative;z-index:5;}}
.nav-avatar-row{{display:flex;align-items:center;gap:9px;}}
.nav-avatar{{width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;background:#6546E3;color:#fff;font-size:.65rem;font-weight:700;flex:0 0 auto;}}
.nav-user-meta{{min-width:0;display:flex;flex-direction:column;justify-content:center;}}
.nav-user{{font-size:.66rem;font-weight:600;color:#fff;line-height:1.15;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.nav-level{{font-size:.57rem;color:#E1DEFF;line-height:1.12;margin-top:5px;}}
.nav-logout-wrap{{border-top:1px solid rgba(255,255,255,.13);padding:5px 0 0;margin:0 -2px;position:relative;z-index:5;}}
[data-testid="stSidebar"] .st-key-nav_logout{{margin:0!important;}}
[data-testid="stSidebar"] .st-key-nav_logout button{{min-height:44px!important;height:44px!important;padding:0 13px!important;font-size:.75rem!important;font-weight:600!important;background:transparent!important;box-shadow:none!important;border:0!important;color:#fff!important;display:grid!important;grid-template-columns:23px minmax(0,1fr)!important;column-gap:11px!important;align-items:center!important;justify-content:stretch!important;text-align:left!important;}}
[data-testid="stSidebar"] .st-key-nav_logout button [data-testid="stMarkdownContainer"]{{grid-column:2!important;margin:0!important;padding:0!important;min-width:0!important;width:100%!important;justify-self:stretch!important;}}
[data-testid="stSidebar"] .st-key-nav_logout button p{{font-size:.75rem!important;font-weight:600!important;color:#fff!important;white-space:nowrap!important;line-height:1.22!important;margin:0!important;padding:0!important;text-align:left!important;}}
.st-key-nav_logout button::before{{grid-column:1!important;width:23px;height:23px;-webkit-mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 4H4v16h6'/%3E%3Cpath d='M13 8l4 4-4 4'/%3E%3Cpath d='M8 12h9'/%3E%3C/svg%3E") center/contain no-repeat;mask:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M10 4H4v16h6'/%3E%3Cpath d='M13 8l4 4-4 4'/%3E%3Cpath d='M8 12h9'/%3E%3C/svg%3E") center/contain no-repeat;}}
[data-testid="stSidebar"] .st-key-nav_logout button:hover{{background:rgba(255,255,255,.05)!important;}}

/* Finalized BRD global header */
.global-student{{font-size:1.02rem;font-weight:800;color:{DARK};padding-top:.25rem;white-space:nowrap;}}
.global-label{{font-size:.62rem;color:{DARK};font-weight:650;margin-bottom:0;text-align:right;white-space:nowrap;}}
.global-updated{{font-size:.58rem;color:#595A72;text-align:right;white-space:nowrap;padding-top:.34rem;}}
/* Shared AS/A selector across Overview, Record Practice Paper and Topic Analysis. */
[data-testid="stSegmentedControl"] button{{font-size:.61rem!important;font-weight:600!important;min-height:34px!important;padding:.18rem .72rem!important;border-radius:5px!important;background:#FFFFFF!important;color:{BRD_BLUE}!important;border-color:#C9C6F7!important;box-shadow:none!important;}}
[data-testid="stSegmentedControl"] [aria-pressed="true"]{{background:{BRD_BLUE}!important;color:#FFFFFF!important;border-color:{BRD_BLUE}!important;}}
.st-key-global_action_wrap{{padding-top:.24rem!important;position:relative!important;z-index:20!important;pointer-events:auto!important;}}
.st-key-global_action_wrap .stButton,.st-key-global_action_wrap .stButton>button{{position:relative!important;z-index:21!important;pointer-events:auto!important;}}
.st-key-global_action_wrap .stButton>button{{font-size:.60rem!important;font-weight:600!important;min-height:36px!important;padding:.24rem .65rem!important;border-radius:5px!important;background:{PURPLE}!important;border-color:{PURPLE}!important;}}

/* Shared BRD visual system */
.brd-page-label{{display:none;}}
div[data-testid="stVerticalBlockBorderWrapper"]{{border-color:{BORDER}!important;border-radius:9px!important;background:#fff;box-shadow:none!important;}}
.brd-subject-title{{font-size:.76rem;font-weight:900;color:#3526D7;display:flex;align-items:center;gap:8px;letter-spacing:.005em;}}
.subject-icon{{width:31px;height:31px;display:inline-flex;align-items:center;justify-content:center;border-radius:7px;background:{PURPLE};color:white;font-weight:900;font-size:.72rem;}}
.brd-subject-meta{{color:{DARK};font-size:.58rem;margin:.35rem 0 .55rem;}}
.brd-metric-card{{position:relative;min-height:92px;background:#fff;border:1px solid #E6E6EF;border-radius:9px;padding:10px 11px;}}
.brd-metric-icon{{position:absolute;left:11px;top:14px;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:{PURPLE};background:#F0EDFF;font-weight:800;font-size:.76rem;}}
.brd-metric-label{{color:{DARK};font-size:.50rem;font-weight:800;letter-spacing:.015em;padding-left:42px;padding-right:0;}}
.brd-metric-value{{color:{DARK};font-size:1.00rem;font-weight:900;line-height:1.08;margin-top:9px;padding-left:42px;}}
.brd-metric-sub{{color:{DARK};font-size:.55rem;margin-top:5px;padding-left:42px;}}
.brd-prediction-card{{background:#fff;border:1px solid #E6E6EF;border-radius:9px;padding:10px 12px;margin:.55rem 0;}}
.brd-prediction-label{{color:{DARK};font-size:.50rem;font-weight:800;letter-spacing:.015em;}}
.brd-prediction-value{{color:{DARK};font-size:.96rem;font-weight:900;margin-top:5px;}}
.brd-prediction-sub{{color:{DARK};font-size:.56rem;margin-top:2px;}}
.brd-subsection-title{{color:{DARK};font-size:.52rem;font-weight:850;letter-spacing:.02em;margin-bottom:.28rem;}}
.brd-priority-row{{padding:5px 0;border-bottom:1px solid #EEEEF3;}}
.brd-priority-topic{{color:{DARK};font-size:.61rem;font-weight:800;}}
.brd-priority-subtopic{{color:{DARK};font-size:.54rem;margin-top:1px;}}
.brd-priority-score{{text-align:right;color:{DARK};font-size:.61rem;font-weight:850;padding-top:3px;}}
.brd-narrative{{min-height:96px;border:1px solid #E7E4FB;border-radius:9px;padding:9px 10px;background:#FBFAFF;}}
.brd-narrative-title{{color:#3526D7;font-size:.50rem;font-weight:900;letter-spacing:.02em;}}
.brd-narrative-text{{color:{DARK};font-size:.58rem;line-height:1.4;margin-top:5px;}}
.tag{{display:inline-block;border-radius:999px;padding:2px 6px;font-size:.48rem;font-weight:850;}}
.tag-purple{{background:#EEE9FF;color:{PURPLE};}}.tag-green{{background:#E8F8F1;color:#08764A;}}.tag-orange{{background:#FFF1E7;color:#C95E00;}}.tag-red{{background:#FCE9ED;color:#D71935;}}
.oneview-footer{{color:#77798E;font-size:.52rem;text-align:left;padding:9px 0 0;}}
button[kind="primary"]{{background:{PURPLE}!important;border-color:{PURPLE}!important;}}
.stProgress>div>div>div>div{{background-color:{PURPLE};}}
[data-testid="stPlotlyChart"]{{border-radius:7px;overflow:hidden;}}
.stButton>button{{border-radius:5px;font-size:.61rem;min-height:31px;}}
.stSelectbox label,.stDateInput label,.stTextInput label,.stNumberInput label{{font-size:.57rem!important;font-weight:650!important;color:{DARK}!important;}}
[data-baseweb="select"]>div,input{{font-size:.61rem!important;}}
@media(max-width:1100px){{[data-testid="stSidebar"]{{min-width:194px!important;max-width:194px!important;width:194px!important;}}[data-testid="stSidebar"]>div:first-child{{width:194px!important;}}.nav-brand-wrap{{height:68px;}}[data-testid="stSidebar"] .stButton>button{{min-height:50px;height:50px;}}.nav-spacer{{height:5vh;min-height:26px;max-height:48px;}}.block-container{{padding-left:.75rem;padding-right:.75rem;}}}}
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
            st.markdown(f"<div style='color:{PURPLE};font-weight:900'>◉ ONEVIEW</div><h2 style='color:{DARK};margin:.35rem 0'>Learning Analytics</h2>", unsafe_allow_html=True)
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


def _set_sidebar(open_state):
    st.session_state.sidebar_open = open_state


def _apply_sidebar_state():
    if st.session_state.get("sidebar_open", True):
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"]{display:block!important;visibility:visible!important;opacity:1!important;transform:translateX(0)!important;margin-left:0!important;}
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            [data-testid="stSidebar"]{display:none!important;visibility:hidden!important;}
            </style>
            """,
            unsafe_allow_html=True,
        )


def render_global_header(user):
    name = student_name(sb, user)
    st.session_state.setdefault("overview_level", "AS Level")
    current = st.session_state.overview_level
    if st.session_state.get("global_exam_level") != current:
        st.session_state.global_exam_level = current
    c1, c2, c3, c4 = st.columns([2.15, 2.7, 3.2, 1.85], vertical_alignment="center", gap="small")
    c1.markdown(f"<div class='global-student'>{name}</div>", unsafe_allow_html=True)
    with c2:
        label, control = st.columns([1.05, 2.15], vertical_alignment="center", gap="small")
        label.markdown("<div class='global-label'>Exam Level:</div>", unsafe_allow_html=True)
        with control:
            selected = st.segmented_control("Exam Level", ["AS Level", "A Level"], key="global_exam_level", label_visibility="collapsed")
            if selected and selected != st.session_state.overview_level:
                st.session_state.overview_level = selected
                st.rerun()
    c3.markdown(f"<div class='global-updated'>▣&nbsp; Last updated: {_last_updated(user.id)}</div>", unsafe_allow_html=True)
    with c4:
        with st.container(key="global_action_wrap"):
            st.button("+  Record Practice Paper", type="primary", use_container_width=True, key="global_record_action", on_click=_go_to, args=("Record Practice Paper",))
    st.divider()


def render_navigation(user):
    pages = [("Overview", "Overview", "nav_overview"),("Record\nPractice Paper", "Record Practice Paper", "nav_record"),("Topic Analysis", "Topic Analysis", "nav_topic")]
    name = student_name(sb, user)
    level = st.session_state.get("overview_level", "AS Level")
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "LE"
    if st.session_state.get("sidebar_open", True):
        with st.sidebar:
            st.button("◀", key="nav_collapse", help="Hide navigation", on_click=_set_sidebar, args=(False,))
            st.markdown("""<div class='nav-brand-wrap'><svg class='nav-logo-svg' viewBox='0 0 48 48' fill='none' xmlns='http://www.w3.org/2000/svg' aria-hidden='true'><circle cx='24' cy='24' r='20.5' stroke='white' stroke-width='1.7'/><path d='M14 31V26M20 31V22M26 31V18M32 31V14' stroke='white' stroke-width='1.8' stroke-linecap='round'/><path d='M13 21.5L19 18L24.5 20.5L33 12' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/><path d='M29.5 12H33V15.5' stroke='white' stroke-width='1.7' stroke-linecap='round' stroke-linejoin='round'/></svg><span class='nav-brand'>ONEVIEW</span></div>""", unsafe_allow_html=True)
            for label, page, key in pages:
                st.button(label,key=key,type="primary" if st.session_state.nav == page else "secondary",use_container_width=True,on_click=_go_to,args=(page,))
            st.markdown("<div class='nav-spacer'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='nav-user-block'><div class='nav-avatar-row'><div class='nav-avatar'>{initials}</div><div class='nav-user-meta'><div class='nav-user'>{name}</div><div class='nav-level'>{level} Student</div></div></div></div>", unsafe_allow_html=True)
            st.markdown("<div class='nav-logout-wrap'>", unsafe_allow_html=True)
            if st.button("Log out", key="nav_logout", use_container_width=True):
                try: sb.auth.sign_out()
                except Exception: pass
                for key in ("user", "access_token", "refresh_token", "nav"): st.session_state.pop(key, None)
                st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        with st.container(key="sidebar_expand_wrap"):
            st.button("▶", key="nav_expand", help="Show navigation", on_click=_set_sidebar, args=(True,))


def app():
    user = current_student()
    if not user:
        login(); return
    pages = ["Overview", "Record Practice Paper", "Topic Analysis"]
    st.session_state.setdefault("nav", "Overview")
    st.session_state.setdefault("sidebar_open", True)
    if st.session_state.nav not in pages: st.session_state.nav = "Overview"
    _apply_sidebar_state()
    render_navigation(user)
    render_global_header(user)
    page = st.session_state.nav
    if page == "Overview": render_overview(sb, user)
    elif page == "Record Practice Paper": render_record_practice(sb, user)
    else: render_topic_analysis(sb, user)


app()