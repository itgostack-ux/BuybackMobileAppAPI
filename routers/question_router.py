from fastapi import APIRouter
from controllers.question_controller import get_questions_controller

router = APIRouter(
    prefix="/api/v1",
    tags=["Questions"]
)


@router.get("/GetQuestions")
def get_questions():

    return get_questions_controller()