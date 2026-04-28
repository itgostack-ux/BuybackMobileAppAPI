from fastapi import APIRouter, Query
from schemas.customer_schema import CustomerPayload
from services.customer_service import get_customer_by_mobile_service
from controllers.customer_controller import get_default_payment_account_controller

from controllers.customer_controller import (
    save_customer,
    get_customers_controller,
    get_all_customers_controller,
    get_customer_by_mobile_controller,
    get_customer_by_ch_customer_id_controller
)

router = APIRouter(
    prefix="/Customer",
    tags=["Customers"]
)


@router.post("/Save")
def save_customer_api(payload: CustomerPayload):
    return save_customer(payload)


@router.get("/GetCustomers")
def get_customers_api(
    customer_id: str = Query(default=None),
    mobile_no: str = Query(default=None)
):
    return get_customers_controller(
        customer_id=customer_id,
        mobile_no=mobile_no
    )

@router.get("/AllCustomers")
def get_all_customers_api():
    return get_all_customers_controller()



@router.get("/GetCustomerByMobile")
def get_customer_by_mobile(mobile_no: str):
    return get_customer_by_mobile_service(mobile_no)


@router.get("/GetCustomerByMobile")
def get_customer_by_mobile_api(mobile_no: str = Query(...)):
    return get_customer_by_mobile_controller(mobile_no)


@router.get("/GetCustomerById")
def get_customer_by_id_api(ch_customer_id: int = Query(...)):
    return get_customer_by_ch_customer_id_controller(ch_customer_id)

@router.get("/GetDefaultPaymentAccount")
def get_default_payment_account_api(
    ch_customer_id: int = Query(...)
):
    return get_default_payment_account_controller(ch_customer_id)