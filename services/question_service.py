from collections import OrderedDict
from repositories.question_repository import (
    get_buyback_question_list_repo,
    get_automated_test_list_repo
)


# =========================================================
# CUSTOMER QUESTIONS SERVICE
# =========================================================
def get_buyback_question_list_service():
    rows = get_buyback_question_list_repo()

    if not rows:
        return {"success": True, "data": []}

    # Static category order
    category_order = ["General", "Physical", "Functional", "Accessories", "Warrenty"]

    category_map = OrderedDict()

    for row in rows:
        category = row.get("QuestionCategory") or "Others"
        qname = row["QuestionName"]

        if category not in category_map:
            category_map[category] = OrderedDict()

        if qname not in category_map[category]:
            category_map[category][qname] = {
                "QuestionName": qname,
                "QuestionText": (row.get("QuestionText") or "").strip(),
                "QuestionType": row.get("QuestionType"),
                "DisplayOrder": row.get("DisplayOrder"),
                "Options": []
            }

        if row.get("OptionValue") is not None:
            option_obj = {
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": float(row.get("PriceImpactPercent") or 0)
            }

            if option_obj not in category_map[category][qname]["Options"]:
                category_map[category][qname]["Options"].append(option_obj)

    final_data = []

    # Static category order
    for category in category_order:
        if category in category_map:
            questions = category_map[category]

            # Sort only General by DisplayOrder
            if category == "General":
                sorted_questions = sorted(
                    questions.values(),
                    key=lambda x: int(x.get("DisplayOrder") or 9999)
                )
                final_data.append({
                    "Category": category,
                    "Questions": sorted_questions
                })
            else:
                final_data.append({
                    "Category": category,
                    "Questions": list(questions.values())
                })

    # Add any extra categories not in static list
    for category, questions in category_map.items():
        if category not in category_order:
            final_data.append({
                "Category": category,
                "Questions": list(questions.values())
            })

    return {
        "success": True,
        "count": len(final_data),
        "data": final_data
    }


# =========================================================
# AUTOMATED TEST SERVICE
# =========================================================
def get_automated_test_list_service():
    rows = get_automated_test_list_repo()

    if not rows:
        return {"success": True, "data": []}

    result = OrderedDict()

    for row in rows:
        qname = row["QuestionName"]

        if qname not in result:
            result[qname] = {
                "QuestionName": qname,
                "QuestionText": (row.get("QuestionText") or "").strip(),
                "QuestionType": row.get("QuestionType"),
                "DisplayOrder": row.get("DisplayOrder"),
                "Options": []
            }

        if row.get("OptionValue") is not None:
            option_obj = {
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": float(row.get("PriceImpactPercent") or 0)
            }

            if option_obj not in result[qname]["Options"]:
                result[qname]["Options"].append(option_obj)

    sorted_result = sorted(
        result.values(),
        key=lambda x: int(x.get("DisplayOrder") or 9999)
    )

    return {
        "success": True,
        "count": len(sorted_result),
        "data": sorted_result
    }