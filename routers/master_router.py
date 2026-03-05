from fastapi import APIRouter
from controllers.master_controller import (
    get_tests_controller,
    get_appointment_types_controller
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Masters"]
)


@router.get("/GetTests")
def get_tests():

    return get_tests_controller()


@router.get("/GetAppointmentTypes")
def get_appointment_types():

    return get_appointment_types_controller()