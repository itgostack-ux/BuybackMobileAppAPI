from services.master_service import (
    get_tests_service,
    get_appointment_types_service
)


def get_tests_controller():

    return get_tests_service()


def get_appointment_types_controller():

    return get_appointment_types_service()