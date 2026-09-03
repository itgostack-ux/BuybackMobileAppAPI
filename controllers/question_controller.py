from services.question_service import (
    get_buyback_question_list_service,
    get_automated_test_list_service,
    get_buyback_questions_by_item_service,
    get_diagnostic_questions_by_platform_service
)
from fastapi.responses import JSONResponse
from pymysql.err import MySQLError


def _database_error_response():
    return JSONResponse(
        status_code=503,
        content={
            "success": False,
            "message": "Database connection failed. Please check MySQL server is running.",
            "data": []
        }
    )


def get_buyback_question_list_controller():
    try:
        return get_buyback_question_list_service()
    except MySQLError:
        return _database_error_response()


def get_automated_test_list_controller():
    try:
        return get_automated_test_list_service()
    except MySQLError:
        return _database_error_response()


def get_buyback_questions_by_item_controller(item_code: str):
    try:
        return get_buyback_questions_by_item_service(item_code)
    except MySQLError:
        return _database_error_response()


def get_diagnostic_questions_by_platform_controller(platform: str):
    try:
        return get_diagnostic_questions_by_platform_service(platform)
    except MySQLError:
        return _database_error_response()
