from datetime import date
import pandas as pd

ERROR_TYPES = [
    "No Error",
    "Conceptual Error",
    "Calculation Error",
    "Careless Error",
    "Application Error",
    "Misread Question",
    "Incomplete Answer",
    "Time Pressure",
    "Forgot Formula / Rule",
]


def get_df(sb, table, select="*", filters=None, order=None, desc=False):
    q = sb.table(table).select(select)
    for col, value in (filters or {}).items():
        q = q.eq(col, value)
    if order:
        q = q.order(order, desc=desc)
    return pd.DataFrame(q.execute().data or [])


def student_name(sb, user):
    df = get_df(sb, "students", "student_id,name", {"student_id": user.id})
    if not df.empty and df.iloc[0]["name"]:
        return df.iloc[0]["name"]
    return user.email.split("@")[0] if user.email else "Student"


def overview_row(sb, user_id, level, subject):
    df = get_df(sb, "v_bi_overview_dashboard", "*", {
        "student_id": user_id, "academic_level": level, "subject": subject
    })
    if not df.empty:
        return df.iloc[0].to_dict()
    return {"available_papers": 0, "papers_completed": 0, "target_status": "Not Set",
            "prediction_state": "More data needed", "trend_status": "More data needed"}


def priorities(sb, user_id, level, subject):
    df = get_df(sb, "v_overview_priority_areas", "*", {
        "student_id": user_id, "academic_level": level, "subject": subject
    })
    return df.sort_values("priority_rank") if not df.empty else df


def save_target(sb, user_id, level, subject, target_type, target_value):
    sb.table("student_practice_targets").upsert({
        "student_id": user_id, "academic_level": level, "subject": subject,
        "target_type": target_type, "target_value": int(target_value)
    }, on_conflict="student_id,academic_level,subject").execute()


def mapping_labels(sb):
    topics = get_df(sb, "topics", "topic_id,topic_name")
    subtopics = get_df(sb, "subtopics", "subtopic_id,subtopic_name")
    qmap = get_df(sb, "question_topics", "question_id,topic_id,subtopic_id")
    smap = get_df(sb, "subpart_topics", "sub_part_id,topic_id,subtopic_id")
    topic_names = dict(zip(topics.get("topic_id", []), topics.get("topic_name", [])))
    subtopic_names = dict(zip(subtopics.get("subtopic_id", []), subtopics.get("subtopic_name", [])))

    def build(frame, id_col):
        out = {}
        if frame.empty:
            return out
        for rid, group in frame.groupby(id_col):
            if len(group) != 1:
                out[rid] = {"Topic": "Mapping error", "Sub-topic": "Mapping error", "mapping_valid": False}
                continue
            row = group.iloc[0]
            topic = topic_names.get(row.get("topic_id"), "")
            subtopic = subtopic_names.get(row.get("subtopic_id"), "")
            out[rid] = {"Topic": topic, "Sub-topic": subtopic, "mapping_valid": bool(topic and subtopic)}
        return out

    return build(qmap, "question_id"), build(smap, "sub_part_id")


def build_grid(sb, paper_id, attempt_id=None):
    questions = get_df(sb, "questions", "question_id,paper_id,question_number,max_marks", {"paper_id": paper_id})
    if questions.empty:
        return pd.DataFrame()

    subparts = get_df(sb, "sub_parts", "sub_part_id,question_id,label,max_marks")
    if not subparts.empty:
        subparts = subparts[subparts["question_id"].isin(questions["question_id"].tolist())]
    qtopics, sptopics = mapping_labels(sb)

    qr_lookup, sr_lookup = {}, {}
    if attempt_id:
        qr = get_df(
            sb, "question_results",
            "question_result_id,question_id,score,marks_lost,error_type",
            {"attempt_id": attempt_id},
        )
        if not qr.empty:
            qr_lookup = {r["question_id"]: r for _, r in qr.iterrows()}
            sr = get_df(sb, "subpart_results", "question_result_id,sub_part_id,score,marks_lost,error_type")
            if not sr.empty:
                sr = sr[sr["question_result_id"].isin(qr["question_result_id"].tolist())]
                sr_lookup = {r["sub_part_id"]: r for _, r in sr.iterrows()}

    rows = []
    questions = questions.copy()
    questions["_n"] = pd.to_numeric(questions["question_number"], errors="coerce")
    for _, q in questions.sort_values(["_n", "question_number"]).iterrows():
        parts = subparts[subparts["question_id"] == q["question_id"]] if not subparts.empty else pd.DataFrame()
        if not parts.empty:
            for _, p in parts.sort_values("label").iterrows():
                prev = sr_lookup.get(p["sub_part_id"], {})
                maximum = float(p["max_marks"])
                stored_lost = prev.get("marks_lost") if hasattr(prev, "get") else None
                if stored_lost is None and prev:
                    stored_lost = max(maximum - float(prev.get("score", 0) or 0), 0)
                mapping = sptopics.get(p["sub_part_id"], qtopics.get(q["question_id"], {}))
                error_type = prev.get("error_type") if hasattr(prev, "get") else None
                if stored_lost == 0:
                    error_type = "No Error"
                rows.append({
                    "question_id": q["question_id"],
                    "sub_part_id": p["sub_part_id"],
                    "Question": f"{q['question_number']}{p['label']}",
                    "Topic": mapping.get("Topic", ""),
                    "Sub-topic": mapping.get("Sub-topic", ""),
                    "Max Marks": maximum,
                    "Marks Lost": None if stored_lost is None else int(stored_lost),
                    "Error Type": error_type,
                    "mapping_valid": mapping.get("mapping_valid", False),
                })
        else:
            prev = qr_lookup.get(q["question_id"], {})
            maximum = float(q["max_marks"])
            stored_lost = prev.get("marks_lost") if hasattr(prev, "get") else None
            if stored_lost is None and prev:
                stored_lost = max(maximum - float(prev.get("score", 0) or 0), 0)
            mapping = qtopics.get(q["question_id"], {})
            error_type = prev.get("error_type") if hasattr(prev, "get") else None
            if stored_lost == 0:
                error_type = "No Error"
            rows.append({
                "question_id": q["question_id"],
                "sub_part_id": None,
                "Question": str(q["question_number"]),
                "Topic": mapping.get("Topic", ""),
                "Sub-topic": mapping.get("Sub-topic", ""),
                "Max Marks": maximum,
                "Marks Lost": None if stored_lost is None else int(stored_lost),
                "Error Type": error_type,
                "mapping_valid": mapping.get("mapping_valid", False),
            })
    return pd.DataFrame(rows)


def validate_grid(grid, total_marks=75):
    errors = []
    total_lost = 0
    for _, row in grid.iterrows():
        question = row["Question"]
        if not bool(row.get("mapping_valid", False)):
            errors.append(f"Question {question}: exactly one Topic and one Sub-topic mapping is required.")
        raw = row.get("Marks Lost")
        if raw is None or str(raw).strip() == "":
            errors.append(f"Question {question}: Marks Lost is required.")
            continue
        try:
            numeric = float(raw)
        except Exception:
            errors.append(f"Question {question}: Marks Lost must be numeric.")
            continue
        if numeric != int(numeric):
            errors.append(f"Question {question}: Marks Lost must be a whole number.")
            continue
        lost = int(numeric)
        maximum = int(float(row["Max Marks"]))
        if lost < 0:
            errors.append(f"Question {question}: Marks Lost cannot be negative.")
        elif lost > maximum:
            errors.append(f"Question {question}: Marks Lost cannot exceed Max Marks ({maximum}).")
        else:
            total_lost += lost
        error_type = row.get("Error Type")
        if lost == 0 and error_type != "No Error":
            errors.append(f"Question {question}: Error Type must be No Error when Marks Lost is 0.")
        if lost > 0 and (not error_type or error_type == "No Error"):
            errors.append(f"Question {question}: select an Error Type when marks are lost.")
        if error_type and error_type not in ERROR_TYPES:
            errors.append(f"Question {question}: invalid Error Type.")
    if total_lost > int(total_marks):
        errors.append(f"Total Marks Lost cannot exceed {int(total_marks)}.")
    return errors


def save_attempt(sb, user, paper, grid, date_completed=None, attempt_id=None):
    maximum = float(paper["total_marks"])
    total_lost = float(pd.to_numeric(grid["Marks Lost"], errors="coerce").sum())
    total_score = maximum - total_lost
    percentage = total_score / maximum * 100 if maximum else 0
    completed_on = date_completed or date.today()

    if not attempt_id:
        existing_attempt = get_df(
            sb, "practice_attempts", "attempt_id",
            {"student_id": user.id, "paper_id": paper["paper_id"], "status": "completed"},
            order="updated_at", desc=True,
        )
        if not existing_attempt.empty:
            attempt_id = existing_attempt.iloc[0]["attempt_id"]

    payload = {
        "student_id": user.id,
        "paper_id": paper["paper_id"],
        "attempt_date": str(completed_on),
        "status": "completed",
        "total_score": total_score,
        "percentage": round(percentage, 2),
    }
    if attempt_id:
        sb.table("practice_attempts").update(payload).eq("attempt_id", attempt_id).execute()
    else:
        attempt_id = sb.table("practice_attempts").insert(payload).execute().data[0]["attempt_id"]

    existing = get_df(sb, "question_results", "question_result_id,question_id", {"attempt_id": attempt_id})
    qr_lookup = dict(zip(existing["question_id"], existing["question_result_id"])) if not existing.empty else {}

    for question_id, rows in grid.groupby("question_id"):
        q_max = float(pd.to_numeric(rows["Max Marks"], errors="coerce").sum())
        q_lost = float(pd.to_numeric(rows["Marks Lost"], errors="coerce").sum())
        q_score = q_max - q_lost
        has_subparts = rows["sub_part_id"].notna().any()
        q_error = None if has_subparts else rows.iloc[0]["Error Type"]
        q_payload = {"score": q_score, "marks_lost": q_lost, "error_type": q_error}
        qr_id = qr_lookup.get(question_id)
        if qr_id:
            sb.table("question_results").update(q_payload).eq("question_result_id", qr_id).execute()
        else:
            q_payload.update({"attempt_id": attempt_id, "question_id": question_id})
            qr_id = sb.table("question_results").insert(q_payload).execute().data[0]["question_result_id"]

        if has_subparts:
            sr = get_df(sb, "subpart_results", "subpart_result_id,sub_part_id", {"question_result_id": qr_id})
            sr_lookup = dict(zip(sr["sub_part_id"], sr["subpart_result_id"])) if not sr.empty else {}
            for _, row in rows.iterrows():
                spid = row["sub_part_id"]
                if not spid:
                    continue
                max_marks = float(row["Max Marks"])
                lost = float(row["Marks Lost"])
                sr_payload = {
                    "score": max_marks - lost,
                    "marks_lost": lost,
                    "error_type": row["Error Type"],
                }
                if spid in sr_lookup:
                    sb.table("subpart_results").update(sr_payload).eq("subpart_result_id", sr_lookup[spid]).execute()
                else:
                    sr_payload.update({"question_result_id": qr_id, "sub_part_id": spid})
                    sb.table("subpart_results").insert(sr_payload).execute()
    return total_score, percentage, attempt_id
