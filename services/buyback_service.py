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