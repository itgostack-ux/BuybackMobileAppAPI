from repositories.customer_repository import (
    save_customer_repo,
    save_customer_address_repo,
    delete_customer_address_repo,
    get_customer_by_mobile_repo,
    validate_gofix_customer_repo,
    get_buyback_customers_repo,
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
        addresses=data.get("addresses"),
        payment_accounts=data.get("payment_accounts")
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

    customer_id = (customer_id or "").strip()

    data = get_customer_orders_appointments_repo(customer_id=customer_id)

    return {
        "success": True,
        "customer_id": data.get("customer_id", customer_id),
        "customer_found": data.get("customer_found", True),
        "message": None if data.get("customer_found", True) else "Customer not found",
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


def validate_gofix_customer_service(mobile_no):

    mobile_no = (mobile_no or "").strip()

    if not mobile_no.isdigit() or not (10 <= len(mobile_no) <= 15):
        return {
            "success": False,
            "is_valid": False,
            "message": "mobile_no must contain 10 to 15 digits",
            "mobile_no": mobile_no,
            "data": None
        }

    customer = validate_gofix_customer_repo(mobile_no)

    if not customer:
        return {
            "success": True,
            "is_valid": False,
            "message": "Not a GoFix customer",
            "mobile_no": mobile_no,
            "data": None
        }

    data = {
        "customer_id": customer.get("name"),
        "customer_name": customer.get("customer_name"),
        "mobile_no": customer.get("mobile_no"),
        "email_id": customer.get("email_id"),
        "ch_customer_id": customer.get("ch_customer_id"),
        "membership_id": customer.get("ch_membership_id"),
        "disabled": int(customer.get("disabled") or 0)
    }

    if data["disabled"]:
        return {
            "success": True,
            "is_valid": False,
            "message": "GoFix customer is disabled",
            "mobile_no": mobile_no,
            "data": data
        }

    return {
        "success": True,
        "is_valid": True,
        "message": "Valid GoFix customer",
        "mobile_no": mobile_no,
        "data": data
    }


def _money(value):
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def get_buyback_customers_service():

    rows = get_buyback_customers_repo()

    data = []

    for row in rows:
        data.append({
            "customer_id": row.get("customer_id"),
            "customer_name": row.get("customer_name"),
            "mobile_no": row.get("mobile_no"),
            "email_id": row.get("email_id"),
            "ch_customer_id": row.get("ch_customer_id"),
            "membership_id": row.get("membership_id"),
            "disabled": int(row.get("disabled") or 0),
            "assessment_count": int(row.get("assessment_count") or 0),
            "order_count": int(row.get("order_count") or 0),
            "latest_assessment": row.get("latest_assessment"),
            "latest_assessment_status": row.get("latest_assessment_status") or None,
            "latest_assessment_price": _money(row.get("latest_assessment_price")),
            "latest_order": row.get("latest_order"),
            "latest_order_status": row.get("latest_order_status") or None,
            "latest_order_price": _money(row.get("latest_order_price")),
            "last_activity": row.get("last_activity")
        })

    return {
        "success": True,
        "count": len(data),
        "data": data
    }
