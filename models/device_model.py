from dataclasses import dataclass
from datetime import datetime


@dataclass
class DeviceService:

    name: str
    device_service_id: int
    device_service_name: str
    is_check: int | None = None
    creation: datetime | None = None
    modified: datetime | None = None