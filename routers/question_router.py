from fastapi import APIRouter,Query

from controllers.question_controller import (
    get_buyback_question_list_controller,
    get_automated_test_list_controller,
    get_buyback_questions_controller,
    get_buyback_tests_controller
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


@router.get("/GetBuybackQuestionsByModel")
def get_buyback_questions(
    item_code: str = Query(...)
):

    return get_buyback_questions_controller(
        item_code
    )
@router.get("/GetBuybackTestsByModel")
def get_buyback_tests(
    item_code: str = Query(...)
):

    return get_buyback_tests_controller(
        item_code
    )