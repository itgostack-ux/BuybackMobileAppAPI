# services/buyback_service.py

from repositories.buyback_repository import BuybackRepository

repo = BuybackRepository()


# ✅ GET PRICE
def get_buyback_details(item_code=None, buyback_price_id=None):

    if not item_code and not buyback_price_id:
        return {"success": False, "message": "Provide item_code or buyback_price_id"}

    result = repo.fetch_buyback_price(item_code, buyback_price_id)

    if not result:
        return {"success": False, "message": "Buyback item not found"}

    return {
        "success": True,
        "message": "Buyback details fetched successfully",
        "data": result
    }


# ✅ CREATE ASSESSMENT (🔥 FIXED LOGIC)
def create_buyback_service(payload: dict):

    price_data = repo.get_base_price(payload["item_code"])

    if not price_data:
        return {"success": False, "message": "Price not found"}

    base_price = float(price_data["current_market_price"])

    # 🔥 SUM LOGIC (NOT MAX)
    total_percent = 0

    for r in payload.get("responses", []):
        percent = repo.get_price_percent(
            r["question_code"],
            r["answer_value"]
        )
        total_percent += percent

    # 🔥 CAP (IMPORTANT — MATCH UI)
    MAX_DEDUCTION_PERCENT = 30
    total_percent = min(total_percent, MAX_DEDUCTION_PERCENT)

    estimated_price = round(
        base_price * (1 - total_percent / 100), 2
    )

    name = repo.create_assessment(payload, estimated_price)

    return {
        "success": True,
        "assessment_name": name,
        "base_price": base_price,
        "depreciation_percent": total_percent,
        "estimated_price": estimated_price
    }