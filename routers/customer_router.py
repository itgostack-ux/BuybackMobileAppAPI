from fastapi import APIRouter, Query
from schemas.customer_schema import (
    CustomerPayload,
    CustomerAddressPayload,
    CustomerSignInPayload,
    CustomerOtpVerifyPayload
)
from controllers.customer_controller import (
    save_customer,
    save_customer_address_controller,
    delete_customer_address_controller,
    customer_sign_in_controller,
    customer_verify_otp_controller,
    get_customers_controller,
    get_all_customers_controller,
    get_customer_addresses_controller,
    get_customer_orders_appointments_controller
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


@router.post("/SaveAddress")
def save_customer_address_api(payload: CustomerAddressPayload):
    return save_customer_address_controller(payload)


@router.delete("/DeleteAddress")
def delete_customer_address_api(
    customer_id: str = Query(...),
    address_id: str = Query(...)
):
    return delete_customer_address_controller(customer_id, address_id)


@router.post("/SignIn")
def customer_sign_in_api(payload: CustomerSignInPayload):
    return customer_sign_in_controller(payload)


@router.post("/VerifyOtp")
def customer_verify_otp_api(payload: CustomerOtpVerifyPayload):
    return customer_verify_otp_controller(payload)


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


@router.get("/GetAddressByCustomerId")
def get_customer_addresses_api(customer_id: str = Query(...)):
    return get_customer_addresses_controller(customer_id)


@router.get("/GetOrdersAndAppointmentsByCustomerId")
def get_customer_orders_appointments_api(customer_id: str = Query(...)):
    return get_customer_orders_appointments_controller(customer_id)


# ==========================================
# GET ALL CUSTOMERS
# ==========================================
@router.get("/AllCustomers", include_in_schema=False)
def get_all_customers_api():
    return get_all_customers_controller()
