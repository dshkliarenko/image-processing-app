from pydantic import BaseModel
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

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