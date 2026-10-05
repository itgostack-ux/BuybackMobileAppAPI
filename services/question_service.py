from repositories.question_repository import (
    get_buyback_question_list_repo,
    get_automated_test_list_repo,
    get_buyback_questions_by_item_repo,
    get_buyback_price_item_repo,
    get_diagnostic_questions_by_platform_repo
)
from repositories.buyback_repository import BuybackRepository
from services import grade_pricing as gp

_price_repo = BuybackRepository()


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


def _yes_no(value):
    if value in [1, "1", True, "Yes", "yes"]:
        return "Yes"
    if value in [0, "0", False, "No", "no"]:
        return "No"
    return value


def _format_question_rows(rows):
    questions = {}

    for row in rows:
        question_name = row["QuestionName"]

        if question_name not in questions:
            questions[question_name] = {
                "QuestionCategory": row.get("QuestionCategory"),
                "DiagnosisType": row.get("DiagnosisType"),
                "QuestionID": row.get("QuestionID"),
                "QuestionName": question_name,
                "QuestionText": row.get("QuestionText"),
                "QuestionCode": row.get("QuestionCode"),
                "QuestionType": row.get("QuestionType"),
                "Mandatory": _yes_no(row.get("Mandatory")),
                "Disabled": _yes_no(row.get("Disabled")),
                "AppliesToBrandFamily": row.get("AppliesToBrandFamily"),
                "Options": []
            }

        if row.get("OptionLabel") is not None:
            questions[question_name]["Options"].append({
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": row.get("PriceImpactPercent")
            })

    return list(questions.values())


def _pricing_info(item_code):
    """
    The ERP grade price table of this phone, for grade-wise pricing.
    Returns {} when the phone has no grade prices, so the reply stays as it was.
    """
    try:
        price_row = _price_repo.get_price_row(item_code)
    except Exception:
        return {}

    table = gp.price_table(price_row)

    if not any(band[grade] for band in table.values() for grade in gp.GRADES):
        return {}

    return {"grade_prices": table}


def _with_warranty_category(data):
    """
    Puts a "Warranty" category first, holding the two questions that choose
    the ERP price band: warranty status and device age. The ERP's own Yes/No
    warranty question is left out, so the customer is not asked twice.
    """
    categories = []

    for category in data:
        questions = [
            question for question in category["Questions"]
            if not gp.is_erp_warranty_question(
                question.get("QuestionCode"), question.get("QuestionText")
            )
        ]

        if questions:
            categories.append({**category, "Questions": questions})

    warranty = {
        "QuestionCategory": gp.WARRANTY_CATEGORY,
        "Questions": gp.pricing_questions()
    }

    return [warranty] + categories


def get_buyback_questions_by_item_service(item_code: str):
    item_code = item_code.strip()

    item = get_buyback_price_item_repo(item_code)
    if not item:
        return {
            "success": False,
            "message": "Item code not found in buyback price master",
            "data": []
        }

    rows = get_buyback_questions_by_item_repo(item_code)
    categories = {}

    for row in rows:
        category_name = row.get("QuestionCategory") or "General"
        question_name = row["QuestionName"]

        if category_name not in categories:
            categories[category_name] = {
                "QuestionCategory": category_name,
                "Questions": {}
            }

        questions = categories[category_name]["Questions"]
        if question_name not in questions:
            questions[question_name] = {
                "QuestionName": question_name,
                "DiagnosisType": row.get("DiagnosisType"),
                "QuestionID": row.get("QuestionID"),
                "QuestionText": row.get("QuestionText"),
                "QuestionCode": row.get("QuestionCode"),
                "QuestionType": row.get("QuestionType"),
                "Mandatory": _yes_no(row.get("Mandatory")),
                "Disabled": _yes_no(row.get("Disabled")),
                "Options": []
            }

        if row.get("OptionLabel") is not None:
            questions[question_name]["Options"].append({
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": row.get("PriceImpactPercent")
            })

    data = []
    for category in categories.values():
        category["Questions"] = list(category["Questions"].values())
        data.append(category)

    pricing = _pricing_info(item_code)

    if pricing:
        data = _with_warranty_category(data)

    return {
        "success": True,
        "item_code": item_code,
        "item_name": item.get("item_name"),
        "brand": item.get("brand"),
        "platform": item.get("platform"),
        "count": sum(len(category["Questions"]) for category in data),
        "data": data,
        **pricing
    }


def get_diagnostic_questions_by_platform_service(platform: str):
    platform = platform.strip().lower()

    platform_map = {
        "android": ["Any", "Android"],
        "ios": ["Any", "Apple", "iOS", "IOS"]
    }

    if platform not in platform_map:
        return {
            "success": False,
            "message": "platform must be android or ios",
            "data": []
        }

    rows = get_diagnostic_questions_by_platform_repo(platform_map[platform])
    data = _format_question_rows(rows)

    return {
        "success": True,
        "platform": platform,
        "count": len(data),
        "data": data
    }
