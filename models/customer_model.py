from pydantic import BaseModel, EmailStr
from typing import Optional


class AddressModel(BaseModel):
    address_line1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[str] = None


class PaymentAccountModel(BaseModel):
    bank_name: Optional[str] = None
    branch: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_no: Optional[str] = None
    ifsc_code: Optional[str] = None


class CustomerCreate(BaseModel):
    customer_name: str
    mobile_no: str
    email_id: Optional[EmailStr] = None
    address: Optional[AddressModel] = None
    payment: Optional[PaymentAccountModel] = None