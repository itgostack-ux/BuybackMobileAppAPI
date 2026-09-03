from repositories.buyback_repository import BuybackRepository

repo = BuybackRepository()


# =========================================================
# API 1: CREATE BASIC ASSESSMENT (RESPONSES ONLY)
# =========================================================
def create_buyback_service(payload: dict):

    price_data = repo.get_base_price(payload["item_code"])

    if not price_data:
        return {"success": False, "message": "Price not found"}

    base_price = float(price_data["current_market_price"])

    # RESPONSE %
    response_percent = 0

    for r in payload.get("responses", []):
        percent = repo.get_price_percent(
            r.get("question_id"),
            r.get("answer_value")
        )
        response_percent += percent

    # CAP
    MAX_PERCENT = 80
    total_percent = min(response_percent, MAX_PERCENT)

    # PRICE
    calculated_price = base_price * (1 - total_percent / 100)

    # FLOOR
    floor_price = repo.get_floor_price(payload["item_code"])
    if not floor_price or floor_price <= 0:
        floor_price = base_price * 0.1

    final_price = max(floor_price, calculated_price)

    # SAVE
    name = repo.create_assessment(payload, final_price)

    return {
        "success": True,
        "assessment_name": name,
        "base_price": round(base_price, 2),
        "total_percent": round(total_percent, 2),
        "calculated_price": round(calculated_price, 2),
        "floor_price": round(floor_price, 2),
        "estimated_price": round(final_price, 2)
    }


# =========================================================
# API 2: CREATE FULL ASSESSMENT (RESP + DIAGNOSTICS)
# =========================================================
def create_full_buyback_service(payload: dict):

    price_data = repo.get_base_price(payload["item_code"])

    if not price_data:
        return {"success": False, "message": "Price not found"}

    base_price = float(price_data["current_market_price"])

    # RESPONSE %
    response_percent = 0

    for r in payload.get("responses", []):
        percent = repo.get_price_percent(
            r.get("question_id"),
            r.get("answer_value")
        )
        response_percent += percent

    # DIAGNOSTIC % (FIXED HERE)
    diagnostic_percent = 0

    for d in payload.get("diagnostics", []):

        percent = repo.get_price_percent(
            d.get("test_code"),   # MUST be BQB-00005, BQB-00006
            d.get("result")       # Pass / Fail
        )

        diagnostic_percent += percent

    # TOTAL % + CAP
    MAX_PERCENT = 80
    total_percent = min(response_percent + diagnostic_percent, MAX_PERCENT)

    # PRICE
    calculated_price = base_price * (1 - total_percent / 100)

    # FLOOR
    floor_price = repo.get_floor_price(payload["item_code"])
    if not floor_price or floor_price <= 0:
        floor_price = base_price * 0.1

    final_price = max(floor_price, calculated_price)

    # SAVE FULL
    name = repo.create_full_assessment(payload, final_price)

    return {
        "success": True,
        "assessment_name": name,
        "base_price": round(base_price, 2),
        "response_percent": round(response_percent, 2),
        "diagnostic_percent": round(diagnostic_percent, 2),
        "total_percent": round(total_percent, 2),
        "calculated_price": round(calculated_price, 2),
        "floor_price": round(floor_price, 2),
        "estimated_price": round(final_price, 2)
    }


def submit_mobile_buyback_answers_service(payload: dict):
    customer = repo.get_customer_for_assessment(payload["customer_id"])
    if not customer:
        return {
            "success": False,
            "message": "Customer not found",
            "data": []
        }

    item = repo.get_item_for_assessment(payload["item_code"])
    if not item:
        return {
            "success": False,
            "message": "Item code not found in buyback price master",
            "data": []
        }

    saved_answers = []
    total_percent = 0

    for index, answer in enumerate(payload.get("answers", []), start=1):
        question_name = answer.get("question_name")
        question_code = answer.get("question_code")

        if not question_name and not question_code:
            return {
                "success": False,
                "message": f"question_name or question_code is required in answer {index}",
                "data": []
            }

        question = repo.get_mapped_question_for_item(
            payload["item_code"],
            question_name=question_name,
            question_code=question_code
        )

        if not question:
            return {
                "success": False,
                "message": f"Question is not mapped for this item in answer {index}",
                "data": []
            }

        percent = repo.get_price_percent(question["name"], answer["answer_value"])
        total_percent += percent

        saved_answers.append({
            "question_name": question["name"],
            "question_code": question["question_code"],
            "question_text": question["question_text"],
            "answer_value": answer["answer_value"],
            "price_impact_percent": percent
        })

    max_percent = 80
    total_percent = min(total_percent, max_percent)
    base_price = float(item["current_market_price"])
    calculated_price = base_price * (1 - total_percent / 100)
    floor_price = float(item["d_grade_oow_11"] or 0)

    if floor_price <= 0:
        floor_price = base_price * 0.1

    estimated_price = max(floor_price, calculated_price)

    assessment_name = repo.create_mobile_answer_assessment(
        payload,
        customer,
        item,
        saved_answers,
        estimated_price
    )

    return {
        "success": True,
        "message": "Buyback answers submitted successfully",
        "assessment_name": assessment_name,
        "customer_id": customer["name"],
        "item_code": item["item_code"],
        "answer_count": len(saved_answers),
        "base_price": round(base_price, 2),
        "total_percent": round(total_percent, 2),
        "calculated_price": round(calculated_price, 2),
        "floor_price": round(floor_price, 2),
        "final_price": round(estimated_price, 2),
        "estimated_price": round(estimated_price, 2),
        "answers": saved_answers
    }


def create_sell_now_service(payload: dict):
    assessment = repo.get_assessment_for_sell_now(payload["assessment_name"])
    if not assessment:
        return {
            "success": False,
            "message": "Assessment not found",
            "data": []
        }

    existing_order = repo.get_order_by_assessment(payload["assessment_name"])
    if existing_order:
        return {
            "success": True,
            "message": "Sell now order already exists",
            "order_name": existing_order["name"],
            "assessment_name": existing_order["buyback_assessment"],
            "customer_id": existing_order["customer"],
            "item_code": existing_order["item"],
            "final_price": float(existing_order["final_price"] or 0),
            "approved_price": float(existing_order["approved_price"] or 0),
            "status": existing_order["status"],
            "workflow_state": existing_order["workflow_state"]
        }

    order_name = repo.create_sell_now_order(payload, assessment)

    final_price = float(assessment["estimated_price"] or 0)

    return {
        "success": True,
        "message": "Sell now order created successfully",
        "order_name": order_name,
        "assessment_name": assessment["name"],
        "customer_id": assessment["customer"],
        "item_code": assessment["item"],
        "item_name": assessment["item_name"],
        "final_price": round(final_price, 2),
        "approved_price": round(final_price, 2),
        "status": "Draft",
        "workflow_state": "Draft"
    }
