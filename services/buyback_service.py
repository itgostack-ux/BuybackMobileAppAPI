from repositories.buyback_repository import BuybackRepository

repo = BuybackRepository()


# ✅ CREATE ASSESSMENT (ENGINE LOGIC)
def create_buyback_service(payload: dict):

    # ─────────────────────────────
    # STEP 1: BASE PRICE
    # ─────────────────────────────
    price_data = repo.get_base_price(payload["item_code"])

    if not price_data:
        return {"success": False, "message": "Price not found"}

    base_price = float(price_data["current_market_price"])

    # ─────────────────────────────
    # STEP 2: DEDUCTIONS
    # ─────────────────────────────
    total_deduction = 0

    for r in payload.get("responses", []):

        question_id = r.get("question_id")
        answer_value = r.get("answer_value")

        percent = repo.get_price_percent(
            question_id,
            answer_value
        )

        amount = base_price * (percent / 100)
        total_deduction += amount

    # ─────────────────────────────
    # STEP 3: RAW PRICE
    # ─────────────────────────────
    calculated_price = base_price - total_deduction

    # ─────────────────────────────
    # STEP 4: FLOOR PRICE
    # ─────────────────────────────
    floor_price = repo.get_floor_price(payload["item_code"])

    if not floor_price or floor_price <= 0:
        floor_price = base_price * 0.1

    # ─────────────────────────────
    # STEP 5: FINAL PRICE
    # ─────────────────────────────
    final_price = max(floor_price, calculated_price)

    # ─────────────────────────────
    # STEP 6: SAVE
    # ─────────────────────────────
    name = repo.create_assessment(payload, final_price)

    # ─────────────────────────────
    # STEP 7: RESPONSE
    # ─────────────────────────────
    return {
        "success": True,
        "assessment_name": name,
        "base_price": round(base_price, 2),
        "total_deduction": round(total_deduction, 2),
        "calculated_price": round(calculated_price, 2),
        "floor_price": round(floor_price, 2),
        "estimated_price": round(final_price, 2)
    }