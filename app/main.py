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

PURPLE = "#5B35D5"
DARK = "#211A4A"
MUTED = "#777A91"

st.markdown(
    f"""
<style>
:root{{--ov-purple:{PURPLE};--ov-dark:{DARK};--ov-muted:{MUTED};}}
.stApp{{background:#F7F8FC;color:#20213A;}}
.block-container{{max-width:1420px;padding:.55rem 1.35rem 1.5rem;}}

/* Finalized BRD compact navigation */
[data-testid="stSidebar"]{{background:linear-gradient(180deg,#20106A 0%,#29117E 52%,#25106E 100%);border-right:0;min-width:188px!important;max-width:188px!important;width:188px!important;}}
[data-testid="stSidebar"]>div:first-child{{width:188px!important;}}
[data-testid="stSidebar"] *{{color:white;}}
[data-testid="stSidebar"] .stButton>button{{width:100%;min-height:40px;border:0;border-radius:7px;box-shadow:none;justify-content:flex-start;text-align:left;font-size:.75rem;font-weight:650;padding:.5rem .65rem;margin:.06rem 0;color:#F5F3FF;background:transparent;}}
[data-testid="stSidebar"] .stButton>button:hover{{background:#38208C;color:white;border:0;}}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{{background:#5B35D5!important;color:white!important;border:0!important;}}
.nav-brand{{font-size:.9rem;font-weight:900;letter-spacing:.035em;padding:.1rem 0 0;}}
.nav-sub{{font-size:.6rem;color:#CFC8FF;margin-bottom:.9rem;}}
.nav-user{{font-size:.72rem;font-weight:800;color:white;}}
.nav-email{{font-size:.57rem;color:#CBC5EF;word-break:break-all;}}

/* Shared global header used by every authenticated page */
.brd-student-name{{font-size:.86rem;font-weight:850;color:{DARK};padding-top:.42rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.brd-last-updated{{text-align:right;color:{MUTED};font-size:.64rem;padding:.42rem 0 .18rem;white-space:nowrap;}}
[data-testid="stSegmentedControl"] button{{font-size:.67rem!important;min-height:31px!important;padding:.18rem .62rem!important;}}
.brd-page-label{{color:{PURPLE};font-size:.69rem;font-weight:900;letter-spacing:.06em;margin:.42rem 0 .62rem;}}

/* Shared Overview / BRD components */
.brd-subject-title{{font-size:.96rem;font-weight:900;color:{DARK};display:flex;align-items:center;gap:7px;}}
.subject-icon{{width:28px;height:28px;display:inline-flex;align-items:center;justify-content:center;border-radius:7px;background:#EFEAFF;color:{PURPLE};font-weight:900;}}
.brd-subject-meta{{color:{MUTED};font-size:.7rem;margin:.24rem 0 .62rem;}}
.brd-metric-card{{position:relative;min-height:102px;background:#fff;border:1px solid #E5E6EF;border-radius:9px;padding:10px 11px;}}
.brd-metric-icon{{position:absolute;right:9px;top:8px;width:23px;height:23px;border-radius:6px;display:flex;align-items:center;justify-content:center;color:{PURPLE};background:#F2EEFF;font-weight:800;font-size:.75rem;}}
.brd-metric-label{{color:#777A91;font-size:.63rem;font-weight:800;letter-spacing:.03em;padding-right:25px;}}
.brd-metric-value{{color:{DARK};font-size:1.24rem;font-weight:900;line-height:1.1;margin-top:8px;}}
.brd-metric-sub{{color:#7D8092;font-size:.68rem;margin-top:4px;}}
.brd-prediction-card{{background:#FCFCFF;border:1px solid #E8E8F1;border-radius:9px;padding:11px 12px;margin:.65rem 0;}}
.brd-prediction-label{{color:#6F7287;font-size:.63rem;font-weight:850;letter-spacing:.03em;}}
.brd-prediction-value{{color:{DARK};font-size:1.12rem;font-weight:900;margin-top:4px;}}
.brd-prediction-sub{{color:#7C7F92;font-size:.68rem;margin-top:2px;}}
.brd-section-title{{color:{DARK};font-size:.75rem;font-weight:900;letter-spacing:.02em;}}
.brd-context{{color:#828497;font-size:.66rem;margin:.08rem 0 .5rem;}}
.brd-target-cell{{min-height:67px;border-right:1px solid #ECECF3;padding:5px 7px;}}
.brd-target-label{{color:#838597;font-size:.59rem;font-weight:800;letter-spacing:.03em;}}
.brd-target-value{{color:{DARK};font-size:.96rem;font-weight:900;margin-top:6px;word-break:break-word;}}
.brd-target-footer{{display:flex;align-items:center;justify-content:space-between;gap:9px;color:#7E8092;font-size:.66rem;margin-top:3px;flex-wrap:wrap;}}
.brd-subsection-title{{color:{DARK};font-size:.68rem;font-weight:900;letter-spacing:.03em;margin-bottom:.32rem;}}
.brd-priority-row{{padding:6px 0;border-bottom:1px solid #EEEFF4;}}
.brd-priority-topic{{color:{DARK};font-size:.76rem;font-weight:850;}}
.brd-priority-subtopic{{color:#7A7D90;font-size:.67rem;margin-top:2px;}}
.brd-priority-score{{text-align:right;color:{DARK};font-size:.76rem;font-weight:850;padding-top:5px;}}
.brd-narrative{{min-height:110px;border:1px solid #E7E7F0;border-radius:9px;padding:10px 11px;background:#FBFBFE;border-left:3px solid {PURPLE};}}
.brd-narrative-title{{color:{PURPLE};font-size:.62rem;font-weight:900;letter-spacing:.03em;}}
.brd-narrative-text{{color:#404158;font-size:.74rem;line-height:1.42;margin-top:6px;}}
.tag{{display:inline-block;border-radius:999px;padding:3px 8px;font-size:.61rem;font-weight:850;}}
.tag-purple{{background:#EEE9FF;color:{PURPLE};}}.tag-green{{background:#E8F8F1;color:#08764A;}}.tag-orange{{background:#FFF4E5;color:#A75B00;}}.tag-red{{background:#FCE9ED;color:#B32B43;}}
.dialog-available,.target-preview{{display:flex;justify-content:space-between;align-items:center;background:#F5F2FF;border:1px solid #E3DCFF;border-radius:8px;padding:9px 11px;margin:.4rem 0 .6rem;color:{DARK};}}
.oneview-footer{{color:#8B8DA1;font-size:.66rem;text-align:center;padding:14px 0 0;}}
button[kind="primary"]{{background:{PURPLE}!important;border-color:{PURPLE}!important;}}
.stProgress>div>div>div>div{{background-color:{PURPLE};}}
div[data-testid="stVerticalBlockBorderWrapper"]{{border-color:#E4E5EE!important;border-radius:9px!important;background:white;box-shadow:none!important;}}
[data-testid="stPlotlyChart"]{{border-radius:8px;overflow:hidden;}}
[data-testid="stMetric"]{{background:transparent;border:0;padding:0;}}
@media(max-width:1100px){{[data-testid="stSidebar"]{{min-width:172px!important;max-width:172px!important;width:172px!important;}}[data-testid="stSidebar"]>div:first-child{{width:172px!important;}}.block-container{{padding-left:.85rem;padding-right:.85rem;}}}}
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
    stamp = pd.to_datetime(
        rows.iloc[0].get("updated_at") or rows.iloc[0].get("created_at"),
        utc=True,
        errors="coerce",
    )
    return "No activity yet" if pd.isna(stamp) else stamp.strftime("%d %b %Y, %I:%M %p")


def render_global_header(user):
    name = student_name(sb, user)
    st.session_state.setdefault("overview_level", "AS Level")
    current = st.session_state.overview_level
    if st.session_state.get("global_exam_level") != current:
        st.session_state.global_exam_level = current

    c1, c2, c3, c4 = st.columns([2.65, 2.05, 2.55, 1.8], vertical_alignment="center")
    c1.markdown(f"<div class='brd-student-name'>{name}</div>", unsafe_allow_html=True)
    with c2:
        selected = st.segmented_control(
            "Exam Level",
            ["AS Level", "A Level"],
            key="global_exam_level",
            label_visibility="collapsed",
        )
        if selected and selected != st.session_state.overview_level:
            st.session_state.overview_level = selected
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
        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)
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
