# routers/buyback_router.py

from fastapi import APIRouter, Query
from typing import Optional

from schemas.buyback_schema import (
    BuybackRequest,
    BuybackPriceResponse,
    BuybackCreateResponse
)

from controllers.buyback_controller import (
    fetch_buyback_controller,
    create_buyback_controller
)

router = APIRouter(prefix="/api/v1", tags=["Buyback"])


@router.get("/buyback-price", response_model=BuybackPriceResponse)
def get_buyback_price(
    item_code: Optional[str] = Query(None),
    buyback_price_id: Optional[str] = Query(None)
):
    return fetch_buyback_controller(item_code, buyback_price_id)


@router.post("/buyback-assessment", response_model=BuybackCreateResponse)
def create_buyback(payload: BuybackRequest):
    return create_buyback_controller(payload.model_dump())