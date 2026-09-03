from fastapi import APIRouter, Query
from schemas.question_schema import (
    SellNowPayload,
    SubmitBuybackQuestionAnswersPayload
)
from controllers.question_controller import (
    get_buyback_question_list_controller,
    get_automated_test_list_controller,
    get_buyback_questions_by_item_controller,
    get_diagnostic_questions_by_platform_controller
)
from controllers.buyback_controller import (
    create_sell_now_controller,
    submit_mobile_buyback_answers_controller
)

router = APIRouter(
    prefix="/api/v2",
    tags=["Buyback Questions"]
)


@router.get("/GetBuybackQuestionList")
def get_buyback_question_list():
    return get_buyback_question_list_controller()


@router.get("/GetAutomatedTestList")
def get_automated_test_list():
    return get_automated_test_list_controller()


@router.get("/GetBuybackQuestionsByItem")
def get_buyback_questions_by_item(item_code: str = Query(...)):
    return get_buyback_questions_by_item_controller(item_code)


@router.get("/GetDiagnosticQuestionsByPlatform")
def get_diagnostic_questions_by_platform(platform: str = Query(..., description="android or ios")):
    return get_diagnostic_questions_by_platform_controller(platform)


@router.post("/SubmitBuybackQuestionAnswers")
def submit_buyback_question_answers(payload: SubmitBuybackQuestionAnswersPayload):
    return submit_mobile_buyback_answers_controller(payload.model_dump())


@router.post("/SellNow")
def create_sell_now(payload: SellNowPayload):
    return create_sell_now_controller(payload.model_dump())
