from pydantic import BaseModel
from typing import Optional


class BuybackPriceResponse(BaseModel):
    buyback_price_id: str
    sku_id: Optional[str]
    item_code: str
    item_name: str
    current_market_price: float
    vendor_price: Optional[float]
    is_active: Optional[int]