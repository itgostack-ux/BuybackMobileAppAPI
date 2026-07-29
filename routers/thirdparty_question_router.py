from fastapi import APIRouter, Query, status

from schemas.thirdparty_buyback_schema import (
    ThirdPartyBuybackRequest
)

from controllers.thirdparty_question_controller import (
    get_thirdparty_buyback_questions_controller,
    create_thirdparty_buyback_controller
)

router = APIRouter(
    prefix="/api/v2/thirdparty",
    tags=["Third Party BuyBack"]
)


# =========================================================
# GET THIRD PARTY BUYBACK QUESTIONS
# =========================================================
@router.get(
    "/GetBuybackQuestions",
    status_code=status.HTTP_200_OK
)
def get_buyback_questions(
    item_code: str = Query(...)
):

    return get_thirdparty_buyback_questions_controller(
        item_code
    )


# =========================================================
# SAVE THIRD PARTY BUYBACK QUESTION RESULT
# =========================================================
@router.post(
    "/BuybackQuestionResult",
    status_code=status.HTTP_201_CREATED
)
def create_buyback_question_result(
    payload: ThirdPartyBuybackRequest
):

    return create_thirdparty_buyback_controller(
        payload.model_dump()
    )