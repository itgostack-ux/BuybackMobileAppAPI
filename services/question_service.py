from collections import OrderedDict

from repositories.question_repository import (
    get_buyback_question_list_repo,
    get_automated_test_list_repo,
    get_buyback_questions_repo,
    get_buyback_tests_repo
)


# =========================================================
# CUSTOMER QUESTIONS SERVICE
# =========================================================
def get_buyback_question_list_service():

    rows = get_buyback_question_list_repo()

    if not rows:
        return {
            "success": True,
            "data": []
        }

    # =====================================================
    # STATIC CATEGORY ORDER
    # =====================================================
    category_order = [
        "General",
        "Physical",
        "Functional",
        "Accessories",
        "Warrenty"
    ]

    # =====================================================
    # FUNCTIONAL QUESTION ORDER
    # =====================================================
    functional_order = [
        "front camera not working",
        "back camera not working",
        "volume button not working",
        "finger touch not working",
        "wifi not working",
        "battery faulty",
        "speaker faulty",
        "power button not working",
        "charging port not working",
        "face sensor not working",
        "silent button not working",
        "audio receiver not working",
        "camera glass broken",
        "blutooth not working",
        "vibrator not working",
        "microphone not working",
        "proximity sensor not working"
    ]

    category_map = OrderedDict()

    # =====================================================
    # BUILD CATEGORY MAP
    # =====================================================
    for row in rows:

        category = row.get("QuestionCategory") or "Others"

        qname = row["QuestionName"]

        if category not in category_map:
            category_map[category] = OrderedDict()

        if qname not in category_map[category]:

            category_map[category][qname] = {
                "QuestionName": qname,
                "QuestionText": (
                    row.get("QuestionText") or ""
                ).strip(),
                "QuestionType": row.get("QuestionType"),
                "DisplayOrder": row.get("DisplayOrder"),
                "Options": []
            }

        # =================================================
        # ADD OPTIONS
        # =================================================
        if row.get("OptionValue") is not None:

            option_obj = {
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": float(
                    row.get("PriceImpactPercent") or 0
                )
            }

            if option_obj not in category_map[category][qname]["Options"]:

                category_map[category][qname]["Options"].append(
                    option_obj
                )

    final_data = []

    # =====================================================
    # PROCESS CATEGORY ORDER
    # =====================================================
    for category in category_order:

        if category not in category_map:
            continue

        questions = list(
            category_map[category].values()
        )

        # =================================================
        # FUNCTIONAL HARDCODED ORDER
        # =================================================
        if category == "Functional":

            ordered_questions = []

            for order_text in functional_order:

                for question in questions:

                    question_text = (
                        question["QuestionText"]
                        .strip()
                        .lower()
                    )

                    if question_text == order_text:

                        ordered_questions.append(
                            question
                        )

                        break

            questions = ordered_questions

        else:

            questions = sorted(
                questions,
                key=lambda x: x[
                    "DisplayOrder"
                ] or 0
            )

        final_data.append({
            "Category": category,
            "Questions": questions
        })

    # =====================================================
    # EXTRA CATEGORIES
    # =====================================================
    for category, questions in category_map.items():

        if category not in category_order:

            final_data.append({
                "Category": category,
                "Questions": sorted(
                    list(questions.values()),
                    key=lambda x: x[
                        "DisplayOrder"
                    ] or 0
                )
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
        return {
            "success": True,
            "data": []
        }

    result = OrderedDict()

    for row in rows:

        qname = row["QuestionName"]

        if qname not in result:

            result[qname] = {
                "QuestionName": qname,
                "QuestionText": (
                    row.get("QuestionText") or ""
                ).strip(),
                "QuestionType": row.get("QuestionType"),
                "DisplayOrder": row.get("DisplayOrder"),
                "Options": []
            }

        # =================================================
        # ADD OPTIONS
        # =================================================
        if row.get("OptionValue") is not None:

            option_obj = {
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": float(
                    row.get("PriceImpactPercent") or 0
                )
            }

            if option_obj not in result[qname]["Options"]:

                result[qname]["Options"].append(
                    option_obj
                )

    return {
        "success": True,
        "count": len(result),
        "data": list(result.values())
    }


# =========================================================
# MODEL BASED QUESTIONS SERVICE
# =========================================================
def get_buyback_questions_service(item_code):

    rows = get_buyback_questions_repo(
        item_code
    )

    if not rows:
        return {
            "success": True,
            "item_code": item_code,
            "data": []
        }

    # =====================================================
    # STATIC CATEGORY ORDER
    # =====================================================
    category_order = [
        "General",
        "Physical",
        "Functional",
        "Accessories",
        "Warrenty"
    ]

    # =====================================================
    # FUNCTIONAL QUESTION ORDER
    # =====================================================
    functional_order = [
        "front camera not working",
        "back camera not working",
        "volume button not working",
        "finger touch not working",
        "wifi not working",
        "battery faulty",
        "speaker faulty",
        "power button not working",
        "charging port not working",
        "face sensor not working",
        "silent button not working",
        "audio receiver not working",
        "camera glass broken",
        "blutooth not working",
        "vibrator not working",
        "microphone not working",
        "proximity sensor not working"
    ]

    category_map = OrderedDict()

    # =====================================================
    # BUILD CATEGORY MAP
    # =====================================================
    for row in rows:

        category = (
            row.get("QuestionCategory")
            or "Others"
        )

        qname = row["QuestionName"]

        if category not in category_map:
            category_map[category] = OrderedDict()

        if qname not in category_map[category]:

            category_map[category][qname] = {
                "QuestionName": qname,
                "QuestionCode": row.get(
                    "QuestionCode"
                ),
                "QuestionText": (
                    row.get("QuestionText") or ""
                ).strip(),
                "QuestionType": row.get(
                    "QuestionType"
                ),
                "DisplayOrder": row.get(
                    "DisplayOrder"
                ),
                "Options": []
            }

        # =================================================
        # ADD OPTIONS
        # =================================================
        if row.get("OptionValue") is not None:

            option_obj = {
                "OptionLabel": row.get(
                    "OptionLabel"
                ),
                "OptionValue": row.get(
                    "OptionValue"
                ),
                "PriceImpactPercent": float(
                    row.get(
                        "PriceImpactPercent"
                    ) or 0
                )
            }

            if (
                option_obj
                not in category_map[category][qname]["Options"]
            ):

                category_map[category][qname][
                    "Options"
                ].append(option_obj)

    final_data = []

    # =====================================================
    # PROCESS CATEGORY ORDER
    # =====================================================
    for category in category_order:

        if category not in category_map:
            continue

        questions = list(
            category_map[category].values()
        )

        # =================================================
        # FUNCTIONAL HARDCODED ORDER
        # =================================================
        if category == "Functional":

            ordered_questions = []

            for order_text in functional_order:

                for question in questions:

                    question_text = (
                        question["QuestionText"]
                        .strip()
                        .lower()
                    )

                    if question_text == order_text:

                        ordered_questions.append(
                            question
                        )

                        break

            questions = ordered_questions

        else:

            questions = sorted(
                questions,
                key=lambda x: x[
                    "DisplayOrder"
                ] or 0
            )

        final_data.append({
            "Category": category,
            "Questions": questions
        })

    # =====================================================
    # EXTRA CATEGORIES
    # =====================================================
    for category, questions in category_map.items():

        if category not in category_order:

            final_data.append({
                "Category": category,
                "Questions": sorted(
                    list(questions.values()),
                    key=lambda x: x[
                        "DisplayOrder"
                    ] or 0
                )
            })

    return {
        "success": True,
        "item_code": item_code,
        "count": len(final_data),
        "data": final_data
    }
# =========================================================
# BUYBACK TESTS SERVICE
# =========================================================
def get_buyback_tests_service(item_code):

    rows = get_buyback_tests_repo(item_code)

    if not rows:
        return {
            "success": True,
            "item_code": item_code,
            "data": []
        }

    result = OrderedDict()

    # =====================================================
    # BUILD TEST MAP
    # =====================================================
    for row in rows:

        test_name = row.get("TestName")

        if test_name not in result:

            result[test_name] = {
                "TestName": test_name,
                "TestCode": row.get("TestCode"),
                "TestText": row.get("TestText"),
                "TestType": row.get("TestType"),
                "TestCategory": row.get("TestCategory"),
                "DisplayOrder": row.get("DisplayOrder"),
                "Options": []
            }

        # =================================================
        # ADD OPTIONS
        # =================================================
        if row.get("OptionValue") is not None:

            option_obj = {
                "OptionLabel": row.get("OptionLabel"),
                "OptionValue": row.get("OptionValue"),
                "PriceImpactPercent": float(
                    row.get("PriceImpactPercent") or 0
                ),
                "OptionOrder": row.get("OptionOrder") or 0
            }

            if (
                option_obj
                not in result[test_name]["Options"]
            ):

                result[test_name]["Options"].append(
                    option_obj
                )

    # =====================================================
    # SORT OPTIONS
    # =====================================================
    for test in result.values():

        test["Options"] = sorted(
            test["Options"],
            key=lambda x: x["OptionOrder"]
        )

        # REMOVE TEMP FIELD
        for opt in test["Options"]:
            opt.pop("OptionOrder", None)

    # =====================================================
    # SORT TESTS
    # =====================================================
    sorted_tests = sorted(
        list(result.values()),
        key=lambda x: x["DisplayOrder"] or 0
    )

    return {
        "success": True,
        "item_code": item_code,
        "count": len(sorted_tests),
        "data": sorted_tests
    }