from repositories.customer_repository import (
    save_customer_repo,
    get_customers_repo
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


def get_all_customers_service():

    data = get_all_customers_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }