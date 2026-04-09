from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional


class AddressSchema(BaseModel):
    address_type: Optional[str] = "Billing"
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = "India"
    pincode: Optional[str] = None
    is_primary_address: Optional[int] = 0


class PaymentAccountSchema(BaseModel):
    account_label: Optional[str] = "Account"
    payment_mode: Optional[str] = None
    is_default: Optional[int] = 0
    bank_name: Optional[str] = None
    branch: Optional[str] = None
    account_holder_name: Optional[str] = None
    account_no: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None


class CustomerPayload(BaseModel):
    customer_id: Optional[str] = None

    customer_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Customer name is required"
    )

    mobile_no: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Mobile number is required"
    )

    email_id: Optional[EmailStr] = None
    disabled: Optional[int] = 0

    addresses: List[AddressSchema] = Field(default_factory=list)
    payment_accounts: List[PaymentAccountSchema] = Field(default_factory=list)

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value):
        if not value.strip():
            raise ValueError("Customer name cannot be empty")
        return value.strip()

    @field_validator("mobile_no")
    @classmethod
    def validate_mobile_no(cls, value):
        if not value.strip():
            raise ValueError("Mobile number cannot be empty")
        if not value.isdigit():
            raise ValueError("Mobile number must contain digits only")
        return value.strip()