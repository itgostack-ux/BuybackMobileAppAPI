from services.customer_service import (
    save_customer_service,
    save_customer_address_service,
    delete_customer_address_service,
    customer_sign_in_service,
    customer_verify_otp_service,
    get_customers_service,
    get_all_customers_service,
    get_customer_addresses_service,
    get_customer_orders_appointments_service
)


def save_customer(payload):
    return save_customer_service(payload)


def save_customer_address_controller(payload):
    return save_customer_address_service(payload)


def delete_customer_address_controller(customer_id, address_id):
    return delete_customer_address_service(customer_id, address_id)


def customer_sign_in_controller(payload):
    return customer_sign_in_service(payload)


def customer_verify_otp_controller(payload):
    return customer_verify_otp_service(payload)


def get_customers_controller(customer_id=None, mobile_no=None):
    return get_customers_service(customer_id, mobile_no)


def get_customer_addresses_controller(customer_id):
    return get_customer_addresses_service(customer_id)


def get_customer_orders_appointments_controller(customer_id):
    return get_customer_orders_appointments_service(customer_id)


def get_all_customers_controller():
    return get_all_customers_service()
