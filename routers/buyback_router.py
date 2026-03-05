from fastapi import APIRouter, Query
from controllers.buyback_controller import fetch_buyback_controller

router = APIRouter(prefix="/api/v1", tags=["Buyback"])


@router.get("/buyback-price")
def get_buyback_price(
    item_code: str | None = Query(None),
    buyback_price_id: str | None = Query(None)
):
    return fetch_buyback_controller(item_code, buyback_price_id)