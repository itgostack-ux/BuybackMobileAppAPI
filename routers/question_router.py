from fastapi import APIRouter
from controllers.question_controller import (
    get_buyback_question_list_controller,
    get_automated_test_list_controller
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