from fastapi import APIRouter, status, HTTPException

from schemas.buyback_schema import (
    BuybackRequest,
    BuybackCreateResponse,
    FullBuybackRequest
)

from controllers.buyback_controller import (
    create_buyback_controller,
    create_full_buyback_controller,
    get_buybacks_with_diagnostics_controller
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Buyback"]
)


# =========================================================
#  API 1: BASIC BUYBACK (RESPONSES ONLY)
# =========================================================
@router.post(
    "/buyback-assessment-questionresult",
    response_model=BuybackCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Buyback Assessment",
    description="Create buyback using question responses only"
)
def create_buyback(payload: BuybackRequest):
    try:
        result = create_buyback_controller(payload.model_dump())

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# =========================================================
#  API 2: FULL BUYBACK (RESPONSES + DIAGNOSTICS)
# =========================================================
@router.post(
    "/buyback-full-assessment-diagonosis",
    response_model=BuybackCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Full Buyback Assessment",
    description="Create buyback with responses and diagnostics"
)
def create_full_buyback(payload: FullBuybackRequest):
    try:
        result = create_full_buyback_controller(payload.model_dump())

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("message"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
@router.get(
    "/GetbuybacksDiagnosticsByCustomerId/{customer_id}",
    summary="Get Buybacks with Diagnostics"
)
def get_buybacks_with_diagnostics(customer_id: str):
    try:
        result = get_buybacks_with_diagnostics_controller()

        if not result.get("success"):
            raise HTTPException(status_code=404, detail=result.get("message"))

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))