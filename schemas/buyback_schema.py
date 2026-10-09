from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from enum import Enum


# =========================================================
# ENUMS
# =========================================================
class TestResult(str, Enum):
    PASS = "Pass"
    FAIL = "Fail"
    YES = "Yes"
    NO = "No"


# =========================================================
# REQUEST MODELS
# =========================================================
class ResponseItem(BaseModel):
    question_id: str = Field(..., example="BQB-00001")
    answer_value: str = Field(..., example="Yes")


class DiagnosticItem(BaseModel):
    test_code: str = Field(..., example="BQB-00006")  # FIXED
    test_name: str = Field(..., example="Bluetooth")
    result: TestResult = Field(..., example="No")


class BuybackRequest(BaseModel):
    customer: str
    customer_name: str
    mobile_no: str = Field(..., pattern="^[0-9]{10}$")

    item_code: str
    item_name: str
    brand: str
    imei_serial: Optional[str] = Field(
        None, example="", description="Optional. Leave it empty when the IMEI is not known"
    )

    source: Optional[str] = "Web"
    company: Optional[str] = None
    item_group: Optional[str] = None
    owner: Optional[str] = "Administrator"

    # The price band of the ERP Price Master. Both are required, unless
    # they are sent as answers of the "Warranty" category
    # (WARRANTY_STATUS and DEVICE_AGE) or the phone is dead.
    warranty_status: Optional[str] = Field(
        None, example="Out of Warranty", description="In Warranty or Out of Warranty"
    )
    device_age_months: Optional[float] = Field(
        None, ge=0, le=600, example=14, description="Age of the phone in months"
    )
    is_phone_dead: Optional[bool] = Field(
        False, description="True when the phone does not switch on: the Phone Dead price is used, grade F"
    )

    responses: List[ResponseItem] = Field(..., min_items=1)

    @field_validator("imei_serial", mode="before")
    @classmethod
    def clean_imei_serial(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None


class FullBuybackRequest(BuybackRequest):
    diagnostics: List[DiagnosticItem] = Field(default_factory=list)


# =========================================================
# RESPONSE MODELS
# =========================================================
class PriceBreakdownItem(BaseModel):
    type: str = Field(..., description="question or diagnostic")
    question_id: str
    question_text: Optional[str] = None
    answer_value: Optional[str] = None
    price_impact_percent: float
    amount: Optional[float] = Field(None, description="The deduction in money: percent of the base price")
    matched: bool = Field(
        ..., description="False when the answer is not one of the question's options"
    )
    counted: Optional[bool] = Field(
        None, description="False when a larger deduction for the same fault was counted instead"
    )
    fault_code: Optional[str] = None


class BuybackCreateResponse(BaseModel):
    success: bool
    assessment_name: str

    base_price: float
    total_percent: float

    calculated_price: float
    floor_price: float
    estimated_price: float

    # How the price was reached. Added so that a price which looks
    # the same for different answers can be explained from the response.
    raw_percent: Optional[float] = None
    response_percent: Optional[float] = None
    diagnostic_percent: Optional[float] = None
    cap_applied: Optional[bool] = None
    floor_applied: Optional[bool] = None
    price_explanation: Optional[str] = None
    breakdown: List[PriceBreakdownItem] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    # The ERP grade pricing: band, grade and the band's grade prices.
    pricing_mode: Optional[str] = Field(None, description="grade, scrap or dead")
    estimated_grade: Optional[str] = Field(None, description="A to D, E for scrap, F for a dead phone")
    price_band: Optional[str] = None
    price_band_label: Optional[str] = None
    warranty_status: Optional[str] = None
    device_age_months: Optional[float] = None
    grade_prices: Optional[Dict[str, Optional[float]]] = None
    total_deductions: Optional[float] = None
    rule_deductions: Optional[float] = Field(None, description="The part of total_deductions that comes from Buyback Pricing Rules")
    max_deduction_percent: Optional[float] = None
    is_scrap: Optional[bool] = None
    is_phone_dead: Optional[bool] = None


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
