from fastapi import HTTPException

from services.thirdparty_question_service import (
    get_thirdparty_buyback_questions_service
)


def get_thirdparty_buyback_questions_controller(item_code):

    try:

        return get_thirdparty_buyback_questions_service(item_code)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )