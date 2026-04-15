# controllers/buyback_controller.py

from fastapi import HTTPException
from services.buyback_service import (
    get_buyback_details,
    create_buyback_service
)


def fetch_buyback_controller(item_code=None, buyback_price_id=None):

    if not item_code and not buyback_price_id:
        raise HTTPException(400, "Provide item_code or buyback_price_id")

    result = get_buyback_details(item_code, buyback_price_id)

    if not result["success"]:
        raise HTTPException(404, result["message"])

    return result


def create_buyback_controller(payload: dict):

    required_fields = [
        "customer",
        "customer_name",
        "mobile_no",
        "item_code",
        "item_name",
        "brand",
        "imei_serial",
        "responses"
    ]

    for f in required_fields:
        if f not in payload or payload[f] in [None, ""]:
            raise HTTPException(400, f"{f} is required")

    result = create_buyback_service(payload)

    if not result["success"]:
        raise HTTPException(400, result["message"])

    return result