from fastapi import APIRouter, Query

from controllers.thirdparty_question_controller import (
    get_thirdparty_buyback_questions_controller
)

router = APIRouter(
    prefix="/api/v2/thirdparty",
    tags=["Third Party BuyBack"]
)


@router.get("/GetBuybackQuestions")
def get_buyback_questions(
    item_code: str = Query(...)
):

    return get_thirdparty_buyback_questions_controller(item_code)