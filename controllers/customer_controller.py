from services.customer_service import (
    save_customer_service,
    get_customers_service,
    get_all_customers_service,
    get_customer_by_ch_customer_id_service,
    get_default_payment_account_service
)


def save_customer(payload):
    return save_customer_service(payload)


def get_customers_controller(customer_id=None, mobile_no=None):
    return get_customers_service(customer_id, mobile_no)


def get_all_customers_controller():
    return get_all_customers_service()

def get_customer_by_mobile_controller(mobile_no: str):
    return get_customer_by_mobile_service(mobile_no)


def get_customer_by_ch_customer_id_controller(ch_customer_id: int):
    return get_customer_by_ch_customer_id_service(ch_customer_id)


def get_default_payment_account_controller(ch_customer_id: int):
    return get_default_payment_account_service(ch_customer_id)