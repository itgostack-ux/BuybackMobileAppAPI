from services.question_service import (
    get_buyback_question_list_service,
    get_automated_test_list_service,
    get_buyback_questions_service,
    get_buyback_tests_service
)


def get_buyback_question_list_controller():
    return get_buyback_question_list_service()


def get_automated_test_list_controller():
    return get_automated_test_list_service()


def get_buyback_questions_controller(item_code):

    return get_buyback_questions_service(
        item_code
    )

def get_buyback_tests_controller(item_code):

    return get_buyback_tests_service(
        item_code
    )