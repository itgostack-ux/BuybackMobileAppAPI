from pydantic import BaseModel, Field
from typing import Optional, List


# =========================
# 1️⃣ GET BUYBACK PRICE
# =========================

class BuybackPriceData(BaseModel):
    buyback_price_id: str
    sku_id: Optional[str] = None
    item_code: str
    item_name: str
    current_market_price: float
    vendor_price: Optional[float] = None
    is_active: Optional[int] = None


class BuybackPriceResponse(BaseModel):
    success: bool
    message: str
    data: BuybackPriceData


# =========================
# 2️⃣ REQUEST MODELS
# =========================

class ResponseItem(BaseModel):
    question_id: str = Field(..., example="BQB-00001")
    answer_value: str = Field(..., example="Yes")


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
# 3️⃣ RESPONSE MODELS
# =========================

class BuybackCreateResponse(BaseModel):
    success: bool
    assessment_name: str
    base_price: float
    total_deduction: float
    calculated_price: float
    floor_price: float
    estimated_price: float


# =========================
# 4️⃣ OPTIONAL (DEBUG / FUTURE)
# =========================

class BuybackResponseDetail(BaseModel):
    question_id: str
    question: Optional[str] = None
    answer_label: str
    price_impact_percent: float


class BuybackDetailedResponse(BaseModel):
    success: bool
    assessment_name: str
    base_price: float
    total_deduction: float
    calculated_price: float
    floor_price: float
    estimated_price: float
    responses: Optional[List[BuybackResponseDetail]] = None