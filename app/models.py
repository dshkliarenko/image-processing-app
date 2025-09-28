from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class ProcessImageResponse(BaseModel):
    success: bool
    image_hash: str
    filename: str
    result: Dict[str, Any]
    processing_time: float
    cache_hit: bool
    timestamp: datetime

class StatusResponse(BaseModel):
    service_ready: bool
    detector_ready: bool
    warmup_completed: bool
    uptime_seconds: float

class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None