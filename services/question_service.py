from collections import defaultdict
from repositories.question_repository import get_questions_repo


def get_questions_service():

    questions, options = get_questions_repo()

    if not questions:
        return {"success": True, "data": {}}

    question_map = {}
    question_type_map = defaultdict(list)

    for q in questions:
        q["options"] = []
        question_map[str(q["QuestionID"])] = q

    for opt in options:
        qid = str(opt["QuestionID"])

        if qid in question_map:
            question_map[qid]["options"].append({
                "OptionID": opt["OptionID"],
                "OptionText": opt["OptionText"],
                "GradeID": opt["GradeID"],
                "GradeName": opt["GradeName"]
            })

    for q in question_map.values():
        question_type_map[q["QuestionType"]].append({
            "QuestionID": q["QuestionID"],
            "QuestionText": q["QuestionText"],
            "QuestionDescription": q.get("QuestionDescription"),
            "options": q["options"]
        })

    return {
        "success": True,
        "data": question_type_map
    }