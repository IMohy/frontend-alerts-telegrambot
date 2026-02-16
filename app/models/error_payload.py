from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ErrorSeverity(str, Enum):
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class DeviceInfo(BaseModel):
    """Device/server information where the error occurred."""
    hostname: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    ip_address: Optional[str] = None
    architecture: Optional[str] = None
    cpu_usage: Optional[float] = Field(None, ge=0, le=100, description="CPU usage percentage")
    memory_usage: Optional[float] = Field(None, ge=0, le=100, description="Memory usage percentage")
    disk_usage: Optional[float] = Field(None, ge=0, le=100, description="Disk usage percentage")


class UserInfo(BaseModel):
    """Information about the user who encountered the error."""
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None


class ErrorContext(BaseModel):
    """Contextual information about the error."""
    request_url: Optional[str] = None
    request_method: Optional[str] = None
    request_headers: Optional[dict[str, str]] = None
    request_body: Optional[str] = None
    response_status: Optional[int] = None
    response_body: Optional[str] = None
    query_params: Optional[dict[str, str]] = None


class ErrorPayload(BaseModel):
    """Main error payload sent to the webhook."""

    # Required fields
    error_message: str = Field(..., min_length=1, max_length=4000, description="The error message")
    severity: ErrorSeverity = Field(default=ErrorSeverity.ERROR, description="Error severity level")

    # Error details
    error_type: Optional[str] = Field(None, description="Exception class name, e.g. ValueError, TypeError")
    error_code: Optional[str] = Field(None, description="Application-specific error code")
    stacktrace: Optional[str] = Field(None, max_length=10000, description="Full stack trace")
    file_name: Optional[str] = Field(None, description="File where the error occurred")
    line_number: Optional[int] = Field(None, ge=0, description="Line number of the error")
    function_name: Optional[str] = Field(None, description="Function/method where the error occurred")

    # Application context
    app_name: Optional[str] = Field(None, description="Name of the application reporting the error")
    app_version: Optional[str] = Field(None, description="Version of the application")
    environment: Optional[str] = Field(None, description="e.g. production, staging, development")
    service_name: Optional[str] = Field(None, description="Microservice name if applicable")
    component: Optional[str] = Field(None, description="Component or module name")

    # Request context
    context: Optional[ErrorContext] = None

    # User context
    user: Optional[UserInfo] = None

    # Device/server info
    device: Optional[DeviceInfo] = None

    # Additional metadata
    tags: Optional[dict[str, str]] = Field(None, description="Key-value tags for categorization")
    metadata: Optional[dict[str, Any]] = Field(None, description="Any additional metadata")

    # Timestamp
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the error occurred")
    fingerprint: Optional[str] = Field(None, description="Unique hash for error grouping/deduplication")


class WebhookResponse(BaseModel):
    """Response returned by the webhook."""
    success: bool
    message: str
    error_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
