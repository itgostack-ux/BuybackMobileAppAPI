from fastapi import APIRouter
from repositories.customer_repository import get_customers_repo
from schemas.customer_schema import CustomerCreate
from controllers.customer_controller import create_customer

router = APIRouter(prefix="/Customer", tags=["Customers"])


@router.post("/")
def create_customer_api(payload: CustomerCreate):
    return create_customer(payload)


@router.get("/GetCustomers")

def get_customers_service():

    data = get_customers_repo()

    return {
        "success": True,
        "count": len(data),
        "data": data
    }