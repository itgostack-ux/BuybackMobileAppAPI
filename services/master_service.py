from repositories.master_repository import (
    get_tests_repo,
    get_appointment_types_repo
)


def get_tests_service():

    data = get_tests_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }


def get_appointment_types_service():

    data = get_appointment_types_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }