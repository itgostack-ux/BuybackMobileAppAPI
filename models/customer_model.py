from pydantic import BaseModel, EmailStr
from typing import Optional


class AddressModel(BaseModel):
    address_line1: Optional[str]
    city: Optional[str]
    state: Optional[str]
    country: Optional[str]
    pincode: Optional[str]


class PaymentAccountModel(BaseModel):
    bank_name: Optional[str]
    branch: Optional[str]
    account_holder_name: Optional[str]
    account_no: Optional[str]
    ifsc_code: Optional[str]


class CustomerCreate(BaseModel):
    customer_name: str
    mobile_no: str
    email_id: Optional[EmailStr]

    address: Optional[AddressModel]
    payment: Optional[PaymentAccountModel]