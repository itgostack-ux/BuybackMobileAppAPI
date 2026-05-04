from collections import defaultdict
from repositories.question_repository import (
    get_buyback_question_list_repo,
    get_automated_test_list_repo
)
def get_buyback_question_list_service():
    rows = get_buyback_question_list_repo()

    if not rows:
        return {"success": True, "data": []}

    category_map = {}

    for row in rows:
        category = row.get("QuestionCategory", "Others")
        qname = row["QuestionName"]

        if category not in category_map:
            category_map[category] = {}

        if qname not in category_map[category]:
            category_map[category][qname] = {
                "QuestionName": qname,
                "QuestionText": row["QuestionText"],
                "QuestionType": row["QuestionType"],
                "Options": []
            }

        if row.get("OptionLabel"):
            category_map[category][qname]["Options"].append({
                "OptionLabel": row["OptionLabel"],
                "OptionValue": row["OptionValue"],
                "PriceImpactPercent": row["PriceImpactPercent"]
            })

    return {
        "success": True,
        "data": [
            {
                "Category": cat,
                "Questions": list(qs.values())
            }
            for cat, qs in category_map.items()
        ]
    }
    
def get_automated_test_list_service():
    rows = get_automated_test_list_repo()

    if not rows:
        return {
            "success": True,
            "data": []
        }

    result = {}

    for row in rows:
        qname = row["QuestionName"]

        if qname not in result:
            result[qname] = {
                "QuestionName": qname,
                "QuestionText": row["QuestionText"],
                "QuestionType": row["QuestionType"],
                "Options": []
            }

        if row["OptionLabel"]:
            result[qname]["Options"].append({
                "OptionLabel": row["OptionLabel"],
                "OptionValue": row["OptionValue"],
                "PriceImpactPercent": row["PriceImpactPercent"]
            })

    return {
        "success": True,
        "data": list(result.values())
    }