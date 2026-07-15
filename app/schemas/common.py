# File: app/schemas/common.py
from datetime import datetime, timezone
from typing import Any, Dict, Generic, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


def get_current_timestamp() -> str:
    """Returns ISO 8601 UTC timestamp string."""
    return datetime.now(timezone.utc).isoformat()


class ErrorDetail(BaseModel):
    """Standardized error payload structure."""
    code: str = Field(..., description="Error classification code")
    message: str = Field(..., description="Human-readable error explanation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional context or validation failure dictionary")


class APIResponse(BaseModel, Generic[DataT]):
    """Standardized API success response wrapper (`5.14 API Response Standard`)."""
    success: bool = True
    message: str = "Request processed successfully"
    data: Optional[DataT] = None
    timestamp: str = Field(default_factory=get_current_timestamp)
    request_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """Standardized API failure response wrapper (`5.14 API Response Standard`)."""
    success: bool = False
    error: ErrorDetail
    timestamp: str = Field(default_factory=get_current_timestamp)
    request_id: Optional[str] = None


def success_response(
    data: Any = None,
    message: str = "Request processed successfully",
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper method to construct a standard APIResponse dictionary."""
    return {
        "success": True,
        "message": message,
        "data": data if data is not None else {},
        "timestamp": get_current_timestamp(),
        "request_id": request_id,
    }


def error_response(
    code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    request_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Helper method to construct a standard ErrorResponse dictionary."""
    return {
        "success": False,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
        },
        "timestamp": get_current_timestamp(),
        "request_id": request_id,
    }
