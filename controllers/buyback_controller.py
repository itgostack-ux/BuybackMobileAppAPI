from fastapi import HTTPException
from services.buyback_service import get_buyback_details


def fetch_buyback_controller(item_code=None, buyback_price_id=None):

    if not item_code and not buyback_price_id:
        raise HTTPException(
            status_code=400,
            detail="Provide item_code or buyback_price_id"
        )

    result = get_buyback_details(item_code, buyback_price_id)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Buyback item not found"
        )

    return result