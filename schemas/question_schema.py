from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class BuybackSelectedAnswer(BaseModel):
    question_name: Optional[str] = Field(None, example="BQB-00001")
    question_code: Optional[str] = Field(None, example="is_the_phone_in_proper_working_condition")
    answer_value: str = Field(..., example="Yes")

    @field_validator("question_name", "question_code", mode="before")
    @classmethod
    def clean_optional_text(cls, value):
        if value is None:
            return None
        value = str(value).strip()
        return value or None

    @field_validator("answer_value")
    @classmethod
    def validate_answer_value(cls, value):
        if not value.strip():
            raise ValueError("answer_value cannot be empty")
        return value.strip()


class SubmitBuybackQuestionAnswersPayload(BaseModel):
    customer_id: str = Field(..., example="6374515589")
    item_code: str = Field(..., example="I08901")
    imei_serial: str = Field(..., example="123456789012345")
    source: Optional[str] = Field("Mobile App", example="Android")
    answers: List[BuybackSelectedAnswer] = Field(..., min_length=1)

    @field_validator("customer_id", "item_code", "imei_serial")
    @classmethod
    def validate_required_text(cls, value):
        if not value.strip():
            raise ValueError("value cannot be empty")
        return value.strip()


class SellNowPayload(BaseModel):
    assessment_name: str = Field(..., example="BBA-2026-00008")
    settlement_type: Optional[str] = Field("Cash", example="Cash")
    customer_payout_mode: Optional[str] = Field(None, example="UPI")
    store: Optional[str] = None
    company: Optional[str] = None
    remarks: Optional[str] = None

    @field_validator("assessment_name")
    @classmethod
    def validate_assessment_name(cls, value):
        if not value.strip():
            raise ValueError("assessment_name cannot be empty")
        return value.strip()
