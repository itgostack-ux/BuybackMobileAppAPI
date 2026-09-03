from repositories.customer_repository import (
    save_customer_repo,
    save_customer_address_repo,
    delete_customer_address_repo,
    get_customer_by_mobile_repo,
    get_customers_repo,
    get_customer_addresses_repo,
    get_customer_orders_appointments_repo
)
from repositories.customer_repository import get_all_customers_repo



def save_customer_service(payload):

    data = payload.dict()

    return save_customer_repo(
        customer_id=data.get("customer_id"),
        customer_name=data.get("customer_name"),
        mobile_no=data.get("mobile_no"),
        email_id=data.get("email_id"),
        disabled=data.get("disabled", 0),
        addresses=data.get("addresses", []),
        payment_accounts=data.get("payment_accounts", [])
    )


def save_customer_address_service(payload):

    data = payload.dict()
    return save_customer_address_repo(data)


def delete_customer_address_service(customer_id, address_id):

    return delete_customer_address_repo(
        customer_id=customer_id,
        address_id=address_id
    )


def customer_sign_in_service(payload):

    data = payload.dict()
    mobile_no = data.get("mobile_no")
    customer = get_customer_by_mobile_repo(mobile_no)

    if not customer:
        return {
            "success": False,
            "message": "No data found",
            "data": None
        }

    return {
        "success": True,
        "message": "OTP sent successfully",
        "mobile_no": mobile_no,
        "otp": "00000",
        "data": customer
    }


def customer_verify_otp_service(payload):

    data = payload.dict()
    mobile_no = data.get("mobile_no")
    otp = data.get("otp")
    customer = get_customer_by_mobile_repo(mobile_no)

    if not customer:
        return {
            "success": False,
            "message": "No data found",
            "data": None
        }

    if otp != "00000":
        return {
            "success": False,
            "message": "Invalid OTP",
            "data": None
        }

    return {
        "success": True,
        "message": "OTP verified successfully",
        "data": customer
    }


def get_customers_service(customer_id=None, mobile_no=None):

    data = get_customers_repo(
        customer_id=customer_id,
        mobile_no=mobile_no
    )

    return {
        "success": True,
        "count": len(data),
        "data": data
    }


def get_customer_addresses_service(customer_id):

    data = get_customer_addresses_repo(customer_id=customer_id)

    return {
        "success": True,
        "customer_id": customer_id,
        "count": len(data),
        "data": data
    }


def get_customer_orders_appointments_service(customer_id):

    data = get_customer_orders_appointments_repo(customer_id=customer_id)

    return {
        "success": True,
        "customer_id": customer_id,
        "orders_count": len(data["orders"]),
        "appointments_count": len(data["appointments"]),
        "orders": data["orders"],
        "appointments": data["appointments"]
    }


def get_all_customers_service():

    data = get_all_customers_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }
