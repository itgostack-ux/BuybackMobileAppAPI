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

    category_map = OrderedDict()

    for row in rows:
        category = row.get("QuestionCategory") or "Others"
        qname = row["QuestionName"]

        # -------------------------
        # CATEGORY LEVEL
        # -------------------------
        if category not in category_map:
            category_map[category] = OrderedDict()

        # -------------------------
        # QUESTION LEVEL
        # -------------------------
        if qname not in category_map[category]:
            category_map[category][qname] = {
                "QuestionName": qname,
                "QuestionText": (row.get("QuestionText") or "").strip(),
                "QuestionType": row.get("QuestionType"),
                "DisplayOrder": row.get("DisplayOrder"),  # ✅ FIXED
                "Options": []
            }

        # -------------------------
        # OPTION LEVEL
        # -------------------------
        if row.get("OptionValue") is not None:
            option_obj = {
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": float(row.get("PriceImpactPercent") or 0)
            }

            # Avoid duplicate options
            if option_obj not in category_map[category][qname]["Options"]:
                category_map[category][qname]["Options"].append(option_obj)

    # -------------------------
    # SORT ONLY GENERAL CATEGORY
    # -------------------------
    for category, questions in category_map.items():
        if category == "General":
            sorted_questions = sorted(
                questions.values(),
                key=lambda x: x.get("DisplayOrder") or 0
            )
            category_map[category] = OrderedDict(
                (q["QuestionName"], q) for q in sorted_questions
            )

    # -------------------------
    # FINAL RESPONSE
    # -------------------------
    return {
        "success": True,
        "count": len(category_map),
        "data": [
            {
                "Category": cat,
                "Questions": list(qs.values())
            }
            for cat, qs in category_map.items()
        ]
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

            # Avoid duplicates
            if option_obj not in result[qname]["Options"]:
                result[qname]["Options"].append(option_obj)

    # -------------------------
    # SORT ALL AUTOMATED TESTS
    # -------------------------
    sorted_result = sorted(
        result.values(),
        key=lambda x: x.get("DisplayOrder") or 0
    )

    return {
        "success": True,
        "count": len(sorted_result),
        "data": sorted_result
    }