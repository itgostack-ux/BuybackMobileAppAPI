from fastapi import APIRouter, status

from schemas.buyback_schema import (
    BuybackRequest,
    BuybackCreateResponse
)

from controllers.buyback_controller import create_buyback_controller

router = APIRouter(
    prefix="/api/v1",
    tags=["Buyback"]
)


@router.post(
    "/buyback-assessment",
    response_model=BuybackCreateResponse,
    status_code=status.HTTP_201_CREATED
)
def create_buyback(payload: BuybackRequest):
    return create_buyback_controller(payload.model_dump())