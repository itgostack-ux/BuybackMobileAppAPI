from fastapi import APIRouter
from controllers.device_controller import get_device_services_controller


router = APIRouter(
    prefix="/api/v1",
    tags=["Device"]
)


@router.get("/GetDeviceServices")
def get_device_services():

    return get_device_services_controller()