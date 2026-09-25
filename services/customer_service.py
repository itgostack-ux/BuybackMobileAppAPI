from fastapi import HTTPException
from repositories.customer_repository import (
    save_customer_repo,
    save_customer_address_repo,
    delete_customer_address_repo,
    get_customer_by_mobile_repo,
    validate_gofix_customer_repo,
    get_customer_buyback_summary_repo,
    get_buyback_customers_repo,
    get_customers_repo,
    get_customer_addresses_repo,
    get_customer_orders_appointments_repo
)
from repositories.customer_repository import get_all_customers_repo
from core import gofix_client



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


def _to_int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _to_money(value):
    try:
        return round(float(value or 0), 2)
    except (TypeError, ValueError):
        return 0.0


def validate_gofix_customer_service(mobile_no):
    """
    GoFix side  : asked from the external GoFix service (IsCustomerExists /
                  ViewCustomerByPhoneNo) -> gofix_message / gofix_response
    Buyback side: looked up in this database (tabCustomer + buyback tables)
                  -> buyback_message / buyback_response
    """

    mobile_no = (mobile_no or "").strip()

    if not mobile_no.isdigit() or len(mobile_no) != 10:
        return {
            "success": False,
            "is_valid": False,
            "mobile_no": mobile_no,
            "gofix_message": "mobile_no must be exactly 10 digits",
            "buyback_message": None,
            "gofix_response": None,
            "buyback_response": None
        }

    # ---------------- GoFix (external service) ----------------
    gofix_exists, gofix_record, gofix_error = gofix_client.lookup_customer(mobile_no)

    if gofix_error:
        gofix_message = f"GoFix check unavailable: {gofix_error}"
        gofix_response = None
    elif gofix_exists:
        gofix_message = "Valid GoFix customer"
        gofix_response = gofix_record or {
            "customer_id": None,
            "customer_name": None,
            "mobile_no": mobile_no,
            "email_id": None,
            "alternate_phone_no": None
        }
    else:
        gofix_message = "Not a GoFix customer"
        gofix_response = None

    # ---------------- Buyback (this database) ----------------
    try:
        customer = validate_gofix_customer_repo(mobile_no)
        buyback_error = None
    except HTTPException as exc:
        customer = None
        buyback_error = exc.detail

    if buyback_error:
        buyback_message = f"Buyback check unavailable: {buyback_error}"
        buyback_response = None
        buyback_exists = False
    elif not customer:
        buyback_message = "Not a buyback customer"
        buyback_response = None
        buyback_exists = False
    else:
        buyback_exists = True
        disabled = _to_int(customer.get("disabled"))
        summary = get_customer_buyback_summary_repo(customer.get("name")) or {}
        assessment_count = _to_int(summary.get("assessment_count"))
        order_count = _to_int(summary.get("order_count"))
        appointment_count = _to_int(summary.get("appointment_count"))

        buyback_response = {
            "customer_id": customer.get("name"),
            "customer_name": customer.get("customer_name"),
            "mobile_no": customer.get("mobile_no"),
            "email_id": customer.get("email_id"),
            "ch_customer_id": customer.get("ch_customer_id"),
            "membership_id": customer.get("ch_membership_id"),
            "disabled": disabled,
            "assessment_count": assessment_count,
            "order_count": order_count,
            "appointment_count": appointment_count,
            "latest_assessment": summary.get("latest_assessment"),
            "latest_assessment_status": summary.get("latest_assessment_status") or None,
            "latest_assessment_price": _to_money(summary.get("latest_assessment_price")),
            "latest_item_name": summary.get("latest_item_name") or None,
            "latest_order": summary.get("latest_order"),
            "latest_order_status": summary.get("latest_order_status") or None,
            "latest_order_price": _to_money(summary.get("latest_order_price")),
            "latest_appointment": summary.get("latest_appointment"),
            "latest_appointment_status": summary.get("latest_appointment_status") or None,
            "last_activity": str(summary.get("last_order_at") or summary.get("last_assessment_at") or "") or None
        }

        if disabled:
            buyback_message = "Buyback customer is disabled"
        elif assessment_count or order_count:
            buyback_message = "Buyback customer"
        else:
            buyback_message = "Registered, no buyback history"

    return {
        "success": True,
        "is_valid": bool(gofix_exists or buyback_exists),
        "mobile_no": mobile_no,
        "gofix_message": gofix_message,
        "buyback_message": buyback_message,
        "gofix_response": gofix_response,
        "buyback_response": buyback_response
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


def is_customer_exists_service(phone):

    phone = (phone or "").strip()

    if not phone.isdigit() or len(phone) != 10:
        return {
            "success": False,
            "exists": False,
            "message": "phone must be exactly 10 digits",
            "phone": phone,
            "data": None
        }

    customer = validate_gofix_customer_repo(phone)

    if not customer:
        return {
            "success": True,
            "exists": False,
            "message": "Customer does not exist",
            "phone": phone,
            "data": None
        }

    return {
        "success": True,
        "exists": True,
        "message": "Customer exists",
        "phone": phone,
        "data": {
            "customer_id": customer.get("name"),
            "customer_name": customer.get("customer_name"),
            "mobile_no": customer.get("mobile_no"),
            "email_id": customer.get("email_id"),
            "ch_customer_id": customer.get("ch_customer_id"),
            "disabled": int(customer.get("disabled") or 0)
        }
    }
