from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


# =========================================================
# ENUMS
# =========================================================
class TestResult(str, Enum):
    PASS = "Pass"
    FAIL = "Fail"


# =========================================================
# REQUEST MODELS
# =========================================================
class ResponseItem(BaseModel):
    question_id: str = Field(..., example="BQB-00001")
    answer_value: str = Field(..., example="Yes")


class DiagnosticItem(BaseModel):
    test_code: str = Field(..., example="BQB-00006")  # FIXED
    test_name: str = Field(..., example="Bluetooth")
    result: TestResult = Field(..., example="Fail")


class BuybackRequest(BaseModel):
    customer: str
    customer_name: str
    mobile_no: str = Field(..., pattern="^[0-9]{10}$")

    item_code: str
    item_name: str
    brand: str
    imei_serial: str

    source: Optional[str] = "Web"
    company: Optional[str] = None
    item_group: Optional[str] = None
    owner: Optional[str] = "Administrator"

    responses: List[ResponseItem] = Field(..., min_items=1)


class FullBuybackRequest(BuybackRequest):
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)


# =========================================================
# RESPONSE MODELS
# =========================================================
class BuybackCreateResponse(BaseModel):
    success: bool
    assessment_name: str

    base_price: float
    total_percent: float

    calculated_price: float
    floor_price: float
    estimated_price: float


# =========================================================
# DEBUG RESPONSE
# =========================================================
class BuybackResponseDetail(BaseModel):
    question_id: str
    question: Optional[str] = None
    answer_label: str
    price_impact_percent: float


class BuybackDiagnosticDetail(BaseModel):
    test_code: str
    test_name: str
    result: TestResult
    depreciation_percent: float


class BuybackDetailedResponse(BaseModel):
    success: bool
    assessment_name: str

    base_price: float
    total_percent: float
    calculated_price: float
    floor_price: float
    estimated_price: float

    responses: List[BuybackResponseDetail] = Field(default_factory=list)
    diagnostics: List[BuybackDiagnosticDetail] = Field(default_factory=list)