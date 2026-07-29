from fastapi import HTTPException

from services.thirdparty_question_service import (
    get_thirdparty_buyback_questions_service,
    create_thirdparty_buyback_service
)


# =========================================================
# GET THIRD PARTY BUYBACK QUESTIONS
# =========================================================
def get_thirdparty_buyback_questions_controller(item_code: str):

    if not item_code:
        raise HTTPException(
            status_code=400,
            detail="item_code is required"
        )

    try:

        result = get_thirdparty_buyback_questions_service(
            item_code
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=404,
                detail=result.get(
                    "message",
                    "Questions not found"
                )
            )

        return result

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )


# =========================================================
# SAVE THIRD PARTY BUYBACK QUESTION RESULT
# =========================================================
def create_thirdparty_buyback_controller(payload: dict):

    # -----------------------------------------------------
    # REQUIRED FIELDS
    # -----------------------------------------------------
    required_fields = [
        "customer",
        "customer_name",
        "mobile_no",
        "item_code",
        "item_name",
        "brand",
        "imei_serial",
        "queAns"
    ]

    for field in required_fields:

        if field not in payload or payload[field] in [None, ""]:

            raise HTTPException(
                status_code=400,
                detail=f"{field} is required"
            )

    # -----------------------------------------------------
    # VALIDATE QUESTION ARRAY
    # -----------------------------------------------------
    que_ans = payload.get("queAns")

    if not isinstance(que_ans, list) or len(que_ans) == 0:

        raise HTTPException(
            status_code=400,
            detail="queAns must be a non-empty list"
        )

    # -----------------------------------------------------
    # VALIDATE EACH QUESTION
    # -----------------------------------------------------
    for index, question in enumerate(que_ans, start=1):

        if not isinstance(question, dict):

            raise HTTPException(
                status_code=400,
                detail=f"Invalid object at queAns[{index}]"
            )

        if not question.get("id"):

            raise HTTPException(
                status_code=400,
                detail=f"id is required in queAns[{index}]"
            )

        if not question.get("data"):

            raise HTTPException(
                status_code=400,
                detail=f"data is required in queAns[{index}]"
            )

    # -----------------------------------------------------
    # CALL SERVICE
    # -----------------------------------------------------
    try:

        result = create_thirdparty_buyback_service(
            payload
        )

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error: {str(e)}"
        )

    # -----------------------------------------------------
    # CHECK RESULT
    # -----------------------------------------------------
    if not result.get("success"):

        raise HTTPException(
            status_code=400,
            detail=result.get(
                "message",
                "Failed to create BuyBack Assessment"
            )
        )

    return result