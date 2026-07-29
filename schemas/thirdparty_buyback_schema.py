from pydantic import BaseModel, Field
from typing import List, Optional


class ThirdPartyQuestionItem(BaseModel):
    id: str
    data: str
    label: Optional[str] = None


class ThirdPartyBuybackRequest(BaseModel):
    customer: str
    customer_name: str
    email: Optional[str] = None
    mobile_no: str = Field(..., pattern="^[0-9]{10}$")

    ch_customer_id: Optional[str] = None

    item_code: str
    item_name: str
    brand: str
    imei_serial: str

    source: Optional[str] = "Web"
    company: Optional[str] = None
    item_group: Optional[str] = None
    owner: Optional[str] = "Administrator"

    queAns: List[ThirdPartyQuestionItem]