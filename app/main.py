import os
from datetime import date

import pandas as pd
import plotly.express as px
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="OneView Learning Analytics",
    page_icon="📘",
    layout="wide"
)

SUPABASE_URL = st.secrets.get(
    "SUPABASE_URL",
    os.getenv("SUPABASE_URL")
)

SUPABASE_ANON_KEY = st.secrets.get(
    "SUPABASE_ANON_KEY",
    os.getenv("SUPABASE_ANON_KEY")
)

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    st.error(
        "Configure SUPABASE_URL and SUPABASE_ANON_KEY "
        "in Streamlit secrets."
    )
    st.stop()

# Create Supabase client
sb = create_client(
    SUPABASE_URL,
    SUPABASE_ANON_KEY
)



def get_df(table, select="*", filters=None):
    q = query(table, select)

    for col, val in (filters or {}).items():
        q = q.eq(col, val)

    r = q.execute()

    return pd.DataFrame(r.data or [])

def query(table, select="*"):
    return sb.table(table).select(select)

def get_df(table, select="*", filters=None):
    q = query(table, select)
    for col, val in (filters or {}).items():
        q = q.eq(col, val)
    r = q.execute()
    return pd.DataFrame(r.data or [])

def login():
    st.title("📘 OneView Learning Analytics")
    st.caption("Cambridge AS Level Mathematics — MVP")

    tab1, tab2 = st.tabs(["Sign in", "Create account"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input(
            "Password",
            type="password",
            key="login_pw"
        )

        if st.button("Sign in", type="primary"):
            try:
                res = sb.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })

                if res.user and res.session:
                    # Save both user and session information
                    st.session_state.user = res.user
                    st.session_state.access_token = res.session.access_token
                    st.session_state.refresh_token = res.session.refresh_token

                    st.success("Sign-in successful.")
                    st.rerun()
                else:
                    st.error("Sign-in succeeded but no session was returned.")

            except Exception as e:
                st.error(f"Sign-in failed: {e}")

    with tab2:
        name = st.text_input(
            "Student name",
            key="reg_name"
        )

        email = st.text_input(
            "Email",
            key="reg_email"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="reg_pw"
        )

        if st.button("Create account"):

            try:
                res = sb.auth.sign_up({
                    "email": email,
                    "password": password
                })

                if res.user:

                    sb.table("students").upsert({
                        "student_id": res.user.id,
                        "name": name,
                        "academic_level": "AS Level",
                        "subject": "Mathematics"
                    }).execute()

                    st.success(
                        "Account created. "
                        "Check your email if confirmation is enabled, "
                        "then sign in."
                    )

            except Exception as e:
                st.error(f"Registration failed: {e}")
def restore_session():
    """
    Restore the Supabase Auth session after Streamlit reruns.
    """

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if not access_token or not refresh_token:
        return None

    try:
        response = sb.auth.set_session(
            access_token,
            refresh_token
        )

        if response and response.user:
            st.session_state.user = response.user
            return response.user

    except Exception:
        pass

    return None
def current_student():
    """
    Restore the Supabase authenticated session on every Streamlit rerun.
    """

    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")

    if access_token and refresh_token:
        try:
            response = sb.auth.set_session(
                access_token,
                refresh_token
            )

            if response and response.user:
                st.session_state.user = response.user

                # Supabase may refresh the tokens
                if response.session:
                    st.session_state.access_token = response.session.access_token
                    st.session_state.refresh_token = response.session.refresh_token

                return response.user

        except Exception as e:
            st.error(f"Could not restore authentication session: {e}")

            st.session_state.pop("user", None)
            st.session_state.pop("access_token", None)
            st.session_state.pop("refresh_token", None)

            return None

    return None
def dashboard(user):
    st.title("Overview Dashboard")
    student_id = user.id
    st.caption(f"Student ID: {student_id}")

    try:
        auth_check = sb.auth.get_user()

        if auth_check and auth_check.user:
            st.success(
                f"Database session authenticated as "
                f"{auth_check.user.email}"
            )
        else:
            st.error("Supabase database session is not authenticated.")

    except Exception as e:
        st.error(f"Auth session test failed: {e}")
    try:
        paper_test = (
            sb.table("exam_papers")
            .select("paper_id,paper_code,year,session")
            .execute()
        )

        attempt_test = (
            sb.table("practice_attempts")
            .select("attempt_id,student_id,total_score")
            .eq("student_id", student_id)
            .execute()
        )

        st.info(
            f"Database check: "
            f"{len(paper_test.data)} papers, "
            f"{len(attempt_test.data)} attempts"
        )

    except Exception as e:
        st.error(f"Database test failed: {e}")
    attempts = get_df("practice_attempts", "attempt_id,student_id,paper_id,attempt_date,total_score,percentage,status", {"student_id": student_id})
    papers = get_df("exam_papers", "paper_id,year,session,paper_code,total_marks")
    if not attempts.empty:
        attempts = attempts[attempts["student_id"] == student_id] if "student_id" in attempts else attempts

    # If RLS/API only returns the student's rows, no further filtering is needed.
    merged = attempts.merge(papers, on="paper_id", how="left") if not attempts.empty and not papers.empty else pd.DataFrame()

    c1,c2,c3,c4 = st.columns(4)
    completed = len(merged)
    avg_pct = float(merged["percentage"].mean()) if completed else 0
    planned = len(papers)
    completion = (completed / planned * 100) if planned else 0
    predicted = float(merged["percentage"].tail(5).mean()) if completed else 0

    c1.metric("Papers completed", completed)
    c2.metric("Planned papers", planned, f"{completion:.1f}% complete")
    c3.metric("Average %", f"{avg_pct:.1f}%")
    c4.metric("Estimated performance", f"{predicted:.1f}%", "V1 estimate")

    if not merged.empty:
        st.subheader("Performance trend")
        trend = merged.sort_values("attempt_date")
        fig = px.line(trend, x="attempt_date", y="percentage", markers=True)
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Topic performance")
    topic = get_df("v_topic_performance", filters={"student_id": student_id})
    if not topic.empty:
        fig = px.bar(topic.sort_values("average_percentage"), x="average_percentage", y="topic_name",
                     orientation="h", title="Average percentage by topic")
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Priority improvement areas")
    weak = get_df("v_topic_performance", filters={"student_id": student_id})
    if weak.empty:
        st.info("Not enough data yet.")
    else:
        weak = weak.sort_values(["marks_lost","average_percentage"], ascending=[False, True]).head(5)
        for _, r in weak.iterrows():
            if r["attempt_count"] >= 2:
                st.warning(f"**{r['topic_name']}** — {r['average_percentage']:.1f}% average; {r['marks_lost']:.1f} marks lost.")

def practice_entry(user):
    st.title("Record Practice Paper")
    papers = get_df("exam_papers")
    if papers.empty:
        st.warning("No papers have been loaded.")
        return

    paper_label = papers.apply(lambda r: f"{r['year']} — {r['session']} — {r['paper_code']}", axis=1)
    selected = st.selectbox("Paper", paper_label)
    paper = papers.iloc[paper_label.tolist().index(selected)]
    st.info(f"Maximum marks: {paper['total_marks']}")

    qs = get_df("questions")
    qs = qs[qs["paper_id"] == paper["paper_id"]].sort_values("question_number")
    sub = get_df("sub_parts")

    answers = []
    total = 0
    invalid = False

    for _, q in qs.iterrows():
        qsubs = sub[sub["question_id"] == q["question_id"]]
        if not qsubs.empty:
            st.markdown(f"### Question {q['question_number']}")
            q_total = 0
            for _, s in qsubs.iterrows():
                val = st.number_input(
                    f"{s['label']} (max {s['max_marks']})",
                    min_value=0.0, max_value=float(s["max_marks"]),
                    value=0.0, step=1.0, key=f"sub_{s['sub_part_id']}"
                )
                if val > float(s["max_marks"]): invalid = True
                q_total += val
                answers.append((q["question_id"], s["sub_part_id"], val))
            total += q_total
        else:
            val = st.number_input(
                f"Question {q['question_number']} (max {q['max_marks']})",
                min_value=0.0, max_value=float(q["max_marks"]),
                value=0.0, step=1.0, key=f"q_{q['question_id']}"
            )
            if val > float(q["max_marks"]): invalid = True
            total += val
            answers.append((q["question_id"], None, val))

    st.metric("Calculated total", f"{total:.1f} / {paper['total_marks']}")
    if invalid:
        st.error("One or more scores exceed the available marks.")
        return

    if st.button("Save completed paper", type="primary"):
        try:
            attempt = sb.table("practice_attempts").insert({
                "student_id": user.id,
                "paper_id": paper["paper_id"],
                "attempt_date": str(date.today()),
                "status": "completed",
                "total_score": total,
                "percentage": total / float(paper["total_marks"]) * 100
            }).execute().data[0]

            for qid, sid, score in answers:
                qr = sb.table("question_results").insert({
                    "attempt_id": attempt["attempt_id"],
                    "question_id": qid,
                    "score": score
                }).execute().data[0]
                if sid:
                    sb.table("subpart_results").insert({
                        "question_result_id": qr["question_result_id"],
                        "sub_part_id": sid,
                        "score": score
                    }).execute()

            st.success("Practice paper saved. Dashboard analytics will now reflect this result.")
            st.rerun()
        except Exception as e:
            st.error(f"Save failed: {e}")

def history(user):
    st.title("Practice History")
    df = get_df("v_attempt_history", filters={"student_id": user.id})
    if df.empty:
        st.info("No completed papers yet.")
    else:
        st.dataframe(df, use_container_width=True)

def insights(user):
    st.title("Intelligent Insights")
    df = get_df("v_topic_performance", filters={"student_id": user.id})
    if df.empty:
        st.info("Insights will appear after enough practice data exists.")
        return
    for _, r in df.sort_values(["marks_lost","average_percentage"], ascending=[False, True]).iterrows():
        if r["attempt_count"] < 2:
            continue
        if r["average_percentage"] < 60:
            st.error(f"**Priority:** {r['topic_name']} — repeated low performance ({r['average_percentage']:.1f}%). Practice more questions from this topic.")
        elif r["average_percentage"] < 75:
            st.warning(f"**Developing:** {r['topic_name']} — {r['average_percentage']:.1f}%. Target this topic in the next practice cycle.")
        else:
            st.success(f"**Strong:** {r['topic_name']} — {r['average_percentage']:.1f}%.")

def app():
    user = current_student()

    if not user:
        login()
        return

    with st.sidebar:
        st.write("### Signed in")
        st.write(user.email)

        page = st.radio(
            "Navigation",
            [
                "Overview",
                "Record Practice",
                "History",
                "Insights",
            ],
        )

        if st.button("Sign out"):
            try:
                sb.auth.sign_out()
            except Exception:
                pass

            st.session_state.pop("user", None)
            st.session_state.pop("access_token", None)
            st.session_state.pop("refresh_token", None)

            st.rerun()

    if page == "Overview":
        dashboard(user)

    elif page == "Record Practice":
        practice_entry(user)

    elif page == "History":
        history(user)

    else:
        insights(user)


app()