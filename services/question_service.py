from collections import defaultdict
from repositories.question_repository import (
    get_buyback_question_list_repo,
    get_automated_test_list_repo
)


def get_buyback_question_list_service():
    rows = get_buyback_question_list_repo()

    if not rows:
        return {
            "success": True,
            "data": []
        }

    question_map = {}

    for row in rows:
        qname = row["QuestionName"]

        if qname not in question_map:
            question_map[qname] = {
                "QuestionName": qname,
                "QuestionText": row["QuestionText"],
                "QuestionType": row["QuestionType"],
                "Options": []
            }

        if row["OptionLabel"]:
            question_map[qname]["Options"].append({
                "OptionLabel": row["OptionLabel"],
                "OptionValue": row["OptionValue"],
                "PriceImpactPercent": row["PriceImpactPercent"]
            })

    return {
        "success": True,
        "data": list(question_map.values())
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