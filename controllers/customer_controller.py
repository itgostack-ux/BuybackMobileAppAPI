from services.customer_service import create_customer_service, get_customers_service


def create_customer(payload):
    return create_customer_service(payload)
def get_customers_controller():

    return get_customers_service()