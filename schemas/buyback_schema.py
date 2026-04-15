from pydantic import BaseModel
from typing import Optional, List


# =========================
# 1. GET BUYBACK PRICE
# =========================

class BuybackPriceData(BaseModel):
    buyback_price_id: str
    sku_id: Optional[str]
    item_code: str
    item_name: str
    current_market_price: float
    vendor_price: Optional[float]
    is_active: Optional[int]


class BuybackPriceResponse(BaseModel):
    success: bool
    message: str
    data: BuybackPriceData


# =========================
# 2. REQUEST MODELS
# =========================

class ResponseItem(BaseModel):
    question_code: str
    answer_value: str


class BuybackRequest(BaseModel):
    customer: str
    customer_name: str
    mobile_no: str

    item_code: str
    item_name: str
    brand: str
    imei_serial: str

    source: Optional[str] = "Web"
    company: Optional[str] = None
    item_group: Optional[str] = None
    owner: Optional[str] = "Administrator"

    responses: List[ResponseItem]


# =========================
# 3. CREATE RESPONSE MODEL
# =========================

class BuybackCreateResponse(BaseModel):
    success: bool
    assessment_name: str
    base_price: float
    depreciation_percent: float
    estimated_price: float


# =========================
# 4. OPTIONAL RESPONSE ITEM (DEBUG / FUTURE)
# =========================

class BuybackResponseDetail(BaseModel):
    question_code: str
    question: Optional[str]
    answer_label: str
    price_impact_percent: float


class BuybackDetailedResponse(BaseModel):
    success: bool
    assessment_name: str
    base_price: float
    depreciation_percent: float
    estimated_price: float
    responses: Optional[List[BuybackResponseDetail]]