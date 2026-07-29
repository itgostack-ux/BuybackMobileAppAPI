from collections import OrderedDict

from repositories.thirdparty_question_repository import (
    get_thirdparty_buyback_questions_repo,
    get_base_price_repo,
    get_price_percent_repo,
    get_floor_price_repo,
    create_thirdparty_buyback_repo
)


# =========================================================
# GET THIRD PARTY BUYBACK QUESTIONS
# =========================================================
def get_thirdparty_buyback_questions_service(item_code):

    rows = get_thirdparty_buyback_questions_repo(item_code)

    result = OrderedDict()

    for row in rows:

        qid = row["QuestionId"]

        if qid not in result:

            result[qid] = {
                "phyEvalId": row["QuestionId"],
                "productId": row["ProductId"],
                "flowId": "BuyBack",
                "elemType": "radio",
                "question": (row["question_text"] or "").strip(),
                "options": [],
                "prodCode": "MOB",
                "status": "active"
            }

        if row["option_value"] is not None:

            result[qid]["options"].append({
                "id": str(row["idx"]),
                "value": row["option_value"],
                "label": row["option_label"]
            })

    return {
        "success": True,
        "statusCode": 200,
        "msg": "Successfully Retrieved",
        "data": {
            "ticketQuePhy": list(result.values())
        }
    }
# =========================================================
# SAVE THIRD PARTY BUYBACK QUESTION RESULT
# =========================================================
def create_thirdparty_buyback_service(payload):

    # -----------------------------------------------------
    # BASE PRICE
    # -----------------------------------------------------
    price_data = get_base_price_repo(
        payload["item_code"]
    )

    if not price_data:
        return {
            "success": False,
            "message": "Price not found"
        }

    base_price = float(
        price_data["current_market_price"]
    )

    # -----------------------------------------------------
    # CALCULATE DEPRECIATION
    # -----------------------------------------------------
    response_percent = 0

    for question in payload.get("queAns", []):

        response_percent += get_price_percent_repo(
            question["id"],
            question["data"]
        )

    MAX_PERCENT = 80

    total_percent = min(
        response_percent,
        MAX_PERCENT
    )

    calculated_price = (
        base_price * (1 - total_percent / 100)
    )

    # -----------------------------------------------------
    # FLOOR PRICE
    # -----------------------------------------------------
    floor_price = get_floor_price_repo(
        payload["item_code"]
    )

    if not floor_price or floor_price <= 0:
        floor_price = base_price * 0.10

    estimated_price = max(
        floor_price,
        calculated_price
    )

    # -----------------------------------------------------
    # REPOSITORY PAYLOAD
    # -----------------------------------------------------
    repo_payload = {
        "customer": payload["customer"],
        "customer_name": payload["customer_name"],
        "mobile_no": payload["mobile_no"],
        "ch_customer_id": payload.get("ch_customer_id"),
        "item_code": payload["item_code"],
        "item_name": payload["item_name"],
        "brand": payload["brand"],
        "imei_serial": payload["imei_serial"],
        "source": payload.get("source", "Web"),
        "company": payload.get("company"),
        "item_group": payload.get("item_group"),
        "owner": payload.get("owner", "Administrator"),

        # Send the same list received from the request
        "queAns": payload.get("queAns", [])
    }

    print("SERVICE PAYLOAD")
    print(repo_payload)
    print("Question Count :", len(repo_payload["queAns"]))

    # -----------------------------------------------------
    # SAVE BUYBACK
    # -----------------------------------------------------
    result = create_thirdparty_buyback_repo(
        repo_payload,
        estimated_price
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------
    return {
        "success": True,
        "statusCode": 201,
        "msg": f"BuyBack Assessment {result['action']} Successfully",
        "data": {
            "assessmentId": result["assessment_name"],
            "action": result["action"],
            "basePrice": round(base_price, 2),
            "depreciationPercent": round(total_percent, 2),
            "calculatedPrice": round(calculated_price, 2),
            "floorPrice": round(floor_price, 2),
            "estimatedPrice": round(estimated_price, 2)
        }
    }