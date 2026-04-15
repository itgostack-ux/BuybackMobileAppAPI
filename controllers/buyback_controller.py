from fastapi import HTTPException
from services.buyback_service import create_buyback_service


# ✅ CREATE BUYBACK ASSESSMENT
def create_buyback_controller(payload: dict):

    # ─────────────────────────────
    # STEP 1: BASIC VALIDATION
    # ─────────────────────────────
    required_fields = [
        "customer",
        "customer_name",
        "mobile_no",
        "item_code",
        "item_name",
        "brand",
        "imei_serial",
        "responses"
    ]

    for field in required_fields:
        if field not in payload or payload[field] in [None, ""]:
            raise HTTPException(
                status_code=400,
                detail=f"{field} is required"
            )

    # ─────────────────────────────
    # STEP 2: VALIDATE RESPONSES
    # ─────────────────────────────
    responses = payload.get("responses")

    if not isinstance(responses, list) or len(responses) == 0:
        raise HTTPException(
            status_code=400,
            detail="responses must be a non-empty list"
        )

    for i, r in enumerate(responses, start=1):

        if not isinstance(r, dict):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid response format at index {i}"
            )

        if not r.get("question_id"):
            raise HTTPException(
                status_code=400,
                detail=f"question_id is required in response {i}"
            )

        if not r.get("answer_value"):
            raise HTTPException(
                status_code=400,
                detail=f"answer_value is required in response {i}"
            )

    # ─────────────────────────────
    # STEP 3: CALL SERVICE
    # ─────────────────────────────
    try:
        result = create_buyback_service(payload)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )

    # ─────────────────────────────
    # STEP 4: HANDLE FAILURE
    # ─────────────────────────────
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("message", "Failed to create assessment")
        )

    # ─────────────────────────────
    # STEP 5: SUCCESS RESPONSE
    # ─────────────────────────────
    return result