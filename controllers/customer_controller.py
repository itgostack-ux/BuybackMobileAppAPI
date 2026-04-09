from services.customer_service import (
    save_customer_service,
    get_customers_service,
    get_all_customers_service
)


def save_customer(payload):
    return save_customer_service(payload)


def get_customers_controller(customer_id=None, mobile_no=None):
    return get_customers_service(customer_id, mobile_no)


def get_all_customers_controller():
    return get_all_customers_service()