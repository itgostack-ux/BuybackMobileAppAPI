from repositories.customer_repository import create_customer_repo, get_customers_repo


def create_customer_service(payload):

    data = payload.dict()

    customer_name = data["customer_name"]
    mobile_no = data["mobile_no"]
    email_id = data.get("email_id")

    address = data.get("address")
    payment = data.get("payment")

    return create_customer_repo(
        customer_name,
        mobile_no,
        email_id,
        address,
        payment
    )


def get_customers_service():

    data = get_customers_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }