from fastapi import APIRouter, Query
from schemas.customer_schema import CustomerPayload
from controllers.customer_controller import (
    save_customer,
    get_customers_controller,
    get_all_customers_controller
)

router = APIRouter(
    prefix="/Customer",
    tags=["Customers"]
)


# ==========================================
# CREATE / UPDATE / ACTIVATE / DISABLE
# ==========================================
@router.post("/Save")
def save_customer_api(payload: CustomerPayload):
    return save_customer(payload)


# ==========================================
# FILTER CUSTOMER BY ID / MOBILE
# ==========================================
@router.get("/GetCustomers")
def get_customers_api(
    customer_id: str = Query(default=None),
    mobile_no: str = Query(default=None)
):
    return get_customers_controller(
        customer_id=customer_id,
        mobile_no=mobile_no
    )


# ==========================================
# GET ALL CUSTOMERS
# ==========================================
@router.get("/AllCustomers")
def get_all_customers_api():
    return get_all_customers_controller()