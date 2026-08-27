from datetime import date
import pandas as pd


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
    tn = dict(zip(topics.get("topic_id", []), topics.get("topic_name", [])))
    sn = dict(zip(subtopics.get("subtopic_id", []), subtopics.get("subtopic_name", [])))
    def build(frame, id_col):
        out = {}
        if frame.empty:
            return out
        for rid, group in frame.groupby(id_col):
            labels = []
            for _, row in group.iterrows():
                topic, sub = tn.get(row.get("topic_id"), ""), sn.get(row.get("subtopic_id"), "")
                label = f"{topic} — {sub}" if topic and sub else topic or sub
                if label and label not in labels:
                    labels.append(label)
            out[rid] = "; ".join(labels)
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
        qr = get_df(sb, "question_results", "question_result_id,question_id,score", {"attempt_id": attempt_id})
        if not qr.empty:
            qr_lookup = {r["question_id"]: r for _, r in qr.iterrows()}
            sr = get_df(sb, "subpart_results", "question_result_id,sub_part_id,score")
            if not sr.empty:
                sr = sr[sr["question_result_id"].isin(qr["question_result_id"].tolist())]
                sr_lookup = {r["sub_part_id"]: float(r["score"]) for _, r in sr.iterrows()}
    rows = []
    questions = questions.copy()
    questions["_n"] = pd.to_numeric(questions["question_number"], errors="coerce")
    for _, q in questions.sort_values(["_n", "question_number"]).iterrows():
        parts = subparts[subparts["question_id"] == q["question_id"]] if not subparts.empty else pd.DataFrame()
        if not parts.empty:
            for _, p in parts.sort_values("label").iterrows():
                rows.append({"question_id": q["question_id"], "sub_part_id": p["sub_part_id"],
                    "Question": str(q["question_number"]), "Sub-part": str(p["label"]),
                    "Maximum Marks": float(p["max_marks"]),
                    "Topic / Subtopic": sptopics.get(p["sub_part_id"], qtopics.get(q["question_id"], "")),
                    "Marks Scored": sr_lookup.get(p["sub_part_id"], 0.0)})
        else:
            prev = qr_lookup.get(q["question_id"], {})
            rows.append({"question_id": q["question_id"], "sub_part_id": None,
                "Question": str(q["question_number"]), "Sub-part": "", "Maximum Marks": float(q["max_marks"]),
                "Topic / Subtopic": qtopics.get(q["question_id"], ""), "Marks Scored": float(prev.get("score", 0) or 0)})
    return pd.DataFrame(rows)


def validate_grid(grid):
    errors = []
    for _, row in grid.iterrows():
        try:
            score = float(row["Marks Scored"] or 0)
        except Exception:
            errors.append(f"Question {row['Question']}: Marks Scored must be numeric.")
            continue
        maximum = float(row["Maximum Marks"])
        if score < 0 or score > maximum:
            errors.append(f"Question {row['Question']} {row['Sub-part']}: score must be between 0 and {maximum:g}.")
    return errors


def save_attempt(sb, user, paper, grid, notes, attempt_id=None):
    total = float(pd.to_numeric(grid["Marks Scored"], errors="coerce").fillna(0).sum())
    maximum = float(paper["total_marks"])
    percentage = total / maximum * 100 if maximum else 0
    payload = {"student_id": user.id, "paper_id": paper["paper_id"], "attempt_date": str(date.today()),
        "status": "completed", "total_score": total, "percentage": round(percentage, 2), "notes": notes.strip() or None}
    if attempt_id:
        sb.table("practice_attempts").update(payload).eq("attempt_id", attempt_id).execute()
    else:
        attempt_id = sb.table("practice_attempts").insert(payload).execute().data[0]["attempt_id"]
    existing = get_df(sb, "question_results", "question_result_id,question_id", {"attempt_id": attempt_id})
    qr_lookup = dict(zip(existing["question_id"], existing["question_result_id"])) if not existing.empty else {}
    for question_id, rows in grid.groupby("question_id"):
        qscore = float(pd.to_numeric(rows["Marks Scored"], errors="coerce").fillna(0).sum())
        qr_id = qr_lookup.get(question_id)
        if qr_id:
            sb.table("question_results").update({"score": qscore}).eq("question_result_id", qr_id).execute()
        else:
            qr_id = sb.table("question_results").insert({"attempt_id": attempt_id, "question_id": question_id, "score": qscore}).execute().data[0]["question_result_id"]
        if rows["sub_part_id"].notna().any():
            sr = get_df(sb, "subpart_results", "subpart_result_id,sub_part_id", {"question_result_id": qr_id})
            sr_lookup = dict(zip(sr["sub_part_id"], sr["subpart_result_id"])) if not sr.empty else {}
            for _, row in rows.iterrows():
                spid = row["sub_part_id"]
                if not spid:
                    continue
                score = float(row["Marks Scored"] or 0)
                if spid in sr_lookup:
                    sb.table("subpart_results").update({"score": score}).eq("subpart_result_id", sr_lookup[spid]).execute()
                else:
                    sb.table("subpart_results").insert({"question_result_id": qr_id, "sub_part_id": spid, "score": score}).execute()
    return total, percentage, attempt_id
