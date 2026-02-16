"""
Jahiz Error Tracker - Client SDK

Drop-in client to report errors to the Jahiz webhook from any Python application.

Usage:
    from client.jahiz_client import JahizClient

    client = JahizClient(
        webhook_url="https://your-server.com/webhook/error",
        webhook_secret="your-secret-here",
        app_name="MyApp",
        environment="production",
    )

    # Report an exception
    try:
        risky_operation()
    except Exception as e:
        client.report_exception(e)

    # Report a custom error
    client.report_error(
        message="Payment processing failed",
        severity="critical",
        error_code="PAY_001",
        metadata={"order_id": "12345", "amount": 99.99},
    )
"""

from __future__ import annotations

import hashlib
import os
import platform
import socket
import sys
import traceback
from datetime import datetime
from typing import Any, Optional

import httpx


class JahizClient:
    """Client for sending error reports to the Jahiz webhook."""

    def __init__(
        self,
        webhook_url: str,
        webhook_secret: str,
        app_name: str | None = None,
        app_version: str | None = None,
        environment: str | None = None,
        service_name: str | None = None,
        timeout: float = 10.0,
        collect_device_info: bool = True,
    ) -> None:
        self.webhook_url = webhook_url.rstrip("/")
        self.webhook_secret = webhook_secret
        self.app_name = app_name
        self.app_version = app_version
        self.environment = environment
        self.service_name = service_name
        self.timeout = timeout
        self.collect_device_info = collect_device_info

    def report_exception(
        self,
        exception: BaseException,
        severity: str = "error",
        component: str | None = None,
        user_id: str | None = None,
        username: str | None = None,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict | None:
        """Report a caught exception to the webhook."""
        tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
        stacktrace = "".join(tb)

        # Extract file/line/function from the traceback
        file_name = None
        line_number = None
        function_name = None
        if exception.__traceback__:
            frame = exception.__traceback__
            while frame.tb_next:
                frame = frame.tb_next
            file_name = frame.tb_frame.f_code.co_filename
            line_number = frame.tb_lineno
            function_name = frame.tb_frame.f_code.co_name

        fingerprint = hashlib.md5(
            f"{type(exception).__name__}:{file_name}:{line_number}".encode()
        ).hexdigest()

        return self.report_error(
            message=str(exception) or type(exception).__name__,
            severity=severity,
            error_type=type(exception).__name__,
            stacktrace=stacktrace,
            file_name=file_name,
            line_number=line_number,
            function_name=function_name,
            fingerprint=fingerprint,
            component=component,
            user_id=user_id,
            username=username,
            tags=tags,
            metadata=metadata,
            context=context,
        )

    def report_error(
        self,
        message: str,
        severity: str = "error",
        error_type: str | None = None,
        error_code: str | None = None,
        stacktrace: str | None = None,
        file_name: str | None = None,
        line_number: int | None = None,
        function_name: str | None = None,
        fingerprint: str | None = None,
        component: str | None = None,
        user_id: str | None = None,
        username: str | None = None,
        email: str | None = None,
        session_id: str | None = None,
        user_ip: str | None = None,
        tags: dict[str, str] | None = None,
        metadata: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
        request_url: str | None = None,
        request_method: str | None = None,
        response_status: int | None = None,
    ) -> dict | None:
        """Send an error report to the webhook."""
        payload: dict[str, Any] = {
            "error_message": message,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Error details
        if error_type:
            payload["error_type"] = error_type
        if error_code:
            payload["error_code"] = error_code
        if stacktrace:
            payload["stacktrace"] = stacktrace
        if file_name:
            payload["file_name"] = file_name
        if line_number is not None:
            payload["line_number"] = line_number
        if function_name:
            payload["function_name"] = function_name
        if fingerprint:
            payload["fingerprint"] = fingerprint

        # Application context
        if self.app_name:
            payload["app_name"] = self.app_name
        if self.app_version:
            payload["app_version"] = self.app_version
        if self.environment:
            payload["environment"] = self.environment
        if self.service_name:
            payload["service_name"] = self.service_name
        if component:
            payload["component"] = component

        # Request context
        ctx: dict[str, Any] = {}
        if request_url:
            ctx["request_url"] = request_url
        if request_method:
            ctx["request_method"] = request_method
        if response_status is not None:
            ctx["response_status"] = response_status
        if context:
            ctx.update(context)
        if ctx:
            payload["context"] = ctx

        # User info
        user_info: dict[str, Any] = {}
        if user_id:
            user_info["user_id"] = user_id
        if username:
            user_info["username"] = username
        if email:
            user_info["email"] = email
        if session_id:
            user_info["session_id"] = session_id
        if user_ip:
            user_info["ip_address"] = user_ip
        if user_info:
            payload["user"] = user_info

        # Device info
        if self.collect_device_info:
            payload["device"] = self._collect_device_info()

        # Tags & metadata
        if tags:
            payload["tags"] = tags
        if metadata:
            payload["metadata"] = metadata

        return self._send(payload)

    def _send(self, payload: dict[str, Any]) -> dict | None:
        """Send payload to the webhook endpoint (synchronous)."""
        try:
            response = httpx.post(
                self.webhook_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Webhook-Secret": self.webhook_secret,
                },
                timeout=self.timeout,
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(
                    f"[JahizClient] Webhook returned {response.status_code}: {response.text}",
                    file=sys.stderr,
                )
                return None
        except Exception as exc:
            print(f"[JahizClient] Failed to send error report: {exc}", file=sys.stderr)
            return None

    async def async_send(self, payload: dict[str, Any]) -> dict | None:
        """Send payload to the webhook endpoint (asynchronous)."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Secret": self.webhook_secret,
                    },
                )
                if response.status_code == 200:
                    return response.json()
                else:
                    print(
                        f"[JahizClient] Webhook returned {response.status_code}: {response.text}",
                        file=sys.stderr,
                    )
                    return None
        except Exception as exc:
            print(f"[JahizClient] Failed to send error report: {exc}", file=sys.stderr)
            return None

    @staticmethod
    def _collect_device_info() -> dict[str, Any]:
        """Collect current machine/server info."""
        import psutil

        info: dict[str, Any] = {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "architecture": platform.machine(),
        }

        try:
            info["cpu_usage"] = psutil.cpu_percent(interval=0.1)
            info["memory_usage"] = psutil.virtual_memory().percent
            info["disk_usage"] = psutil.disk_usage("/").percent
        except Exception:
            pass

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            info["ip_address"] = s.getsockname()[0]
            s.close()
        except Exception:
            pass

        return info
