from __future__ import annotations

import logging
from datetime import datetime

import httpx

from app.core.config import get_settings
from app.models.error_payload import ErrorPayload, ErrorSeverity

logger = logging.getLogger(__name__)

SEVERITY_EMOJI = {
    ErrorSeverity.CRITICAL: "\U0001f534",  # Red circle
    ErrorSeverity.ERROR: "\U0001f7e0",     # Orange circle
    ErrorSeverity.WARNING: "\U0001f7e1",   # Yellow circle
    ErrorSeverity.INFO: "\U0001f535",       # Blue circle
}

SEVERITY_LABEL = {
    ErrorSeverity.CRITICAL: "CRITICAL",
    ErrorSeverity.ERROR: "ERROR",
    ErrorSeverity.WARNING: "WARNING",
    ErrorSeverity.INFO: "INFO",
}


class TelegramService:
    """Service for sending formatted error notifications to Telegram."""

    BASE_URL = "https://api.telegram.org/bot{token}"

    def __init__(self) -> None:
        settings = get_settings()
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID
        self.max_stacktrace = settings.MAX_STACKTRACE_LENGTH
        self.max_metadata = settings.MAX_METADATA_LENGTH
        self.api_url = self.BASE_URL.format(token=self.bot_token)

    async def send_error_notification(
        self, payload: ErrorPayload, error_id: str
    ) -> bool:
        """Format and send an error notification to Telegram."""
        message = self._format_message(payload, error_id)

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{self.api_url}/sendMessage",
                    json={
                        "chat_id": self.chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    },
                )

                if response.status_code != 200:
                    logger.error(
                        "Telegram API error: %s - %s",
                        response.status_code,
                        response.text,
                    )
                    return False

                data = response.json()
                if not data.get("ok"):
                    logger.error("Telegram response not ok: %s", data)
                    return False

                return True

        except httpx.TimeoutException:
            logger.error("Telegram API request timed out")
            return False
        except Exception as exc:
            logger.error("Failed to send Telegram message: %s", exc)
            return False

    async def verify_bot(self) -> dict | None:
        """Verify the bot token is valid by calling getMe."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.api_url}/getMe")
                if response.status_code == 200:
                    return response.json().get("result")
                return None
        except Exception as exc:
            logger.error("Failed to verify bot: %s", exc)
            return None

    def _format_message(self, payload: ErrorPayload, error_id: str) -> str:
        """Build a rich HTML-formatted Telegram message from the error payload."""
        settings = get_settings()
        emoji = SEVERITY_EMOJI.get(payload.severity, "\u26aa")
        label = SEVERITY_LABEL.get(payload.severity, "UNKNOWN")

        parts: list[str] = []

        # Header
        parts.append(
            f"{emoji} <b>{label}</b> | <code>{error_id}</code>"
        )
        parts.append("")

        # Error message
        parts.append(f"<b>Message:</b> {_escape(payload.error_message)}")

        # Error type & code
        if payload.error_type:
            parts.append(f"<b>Type:</b> <code>{_escape(payload.error_type)}</code>")
        if payload.error_code:
            parts.append(f"<b>Code:</b> <code>{_escape(payload.error_code)}</code>")

        # Location
        location_parts = []
        if payload.file_name:
            location_parts.append(payload.file_name)
        if payload.line_number is not None:
            location_parts.append(f"line {payload.line_number}")
        if payload.function_name:
            location_parts.append(f"in {payload.function_name}()")
        if location_parts:
            parts.append(f"<b>Location:</b> <code>{_escape(' | '.join(location_parts))}</code>")

        parts.append("")

        # Application info
        app_lines = []
        if payload.app_name:
            app_lines.append(f"  App: {_escape(payload.app_name)}")
        if payload.app_version:
            app_lines.append(f"  Version: {_escape(payload.app_version)}")
        if payload.environment:
            app_lines.append(f"  Env: {_escape(payload.environment)}")
        if payload.service_name:
            app_lines.append(f"  Service: {_escape(payload.service_name)}")
        if payload.component:
            app_lines.append(f"  Component: {_escape(payload.component)}")

        if app_lines:
            parts.append("<b>Application</b>")
            parts.extend(app_lines)
            parts.append("")

        # Request context
        if payload.context:
            ctx = payload.context
            ctx_lines = []
            if ctx.request_method and ctx.request_url:
                ctx_lines.append(
                    f"  {_escape(ctx.request_method)} {_escape(ctx.request_url)}"
                )
            elif ctx.request_url:
                ctx_lines.append(f"  URL: {_escape(ctx.request_url)}")
            if ctx.response_status is not None:
                ctx_lines.append(f"  Status: {ctx.response_status}")
            if ctx.query_params:
                params_str = ", ".join(
                    f"{k}={v}" for k, v in ctx.query_params.items()
                )
                ctx_lines.append(f"  Params: {_escape(params_str)}")

            if ctx_lines:
                parts.append("<b>Request</b>")
                parts.extend(ctx_lines)
                parts.append("")

        # User info
        if payload.user:
            u = payload.user
            user_lines = []
            if u.user_id:
                user_lines.append(f"  ID: <code>{_escape(u.user_id)}</code>")
            if u.username:
                user_lines.append(f"  Username: {_escape(u.username)}")
            if u.email:
                user_lines.append(f"  Email: {_escape(u.email)}")
            if u.session_id:
                user_lines.append(f"  Session: <code>{_escape(u.session_id)}</code>")
            if u.ip_address:
                user_lines.append(f"  IP: <code>{_escape(u.ip_address)}</code>")

            if user_lines:
                parts.append("<b>User</b>")
                parts.extend(user_lines)
                parts.append("")

        # Device / server info
        if payload.device:
            d = payload.device
            dev_lines = []
            if d.hostname:
                dev_lines.append(f"  Host: <code>{_escape(d.hostname)}</code>")
            if d.os:
                os_str = d.os
                if d.os_version:
                    os_str += f" {d.os_version}"
                dev_lines.append(f"  OS: {_escape(os_str)}")
            if d.ip_address:
                dev_lines.append(f"  IP: <code>{_escape(d.ip_address)}</code>")
            if d.architecture:
                dev_lines.append(f"  Arch: {_escape(d.architecture)}")

            resource_parts = []
            if d.cpu_usage is not None:
                resource_parts.append(f"CPU {d.cpu_usage:.1f}%")
            if d.memory_usage is not None:
                resource_parts.append(f"MEM {d.memory_usage:.1f}%")
            if d.disk_usage is not None:
                resource_parts.append(f"DISK {d.disk_usage:.1f}%")
            if resource_parts:
                dev_lines.append(f"  Resources: {' | '.join(resource_parts)}")

            if dev_lines:
                parts.append("<b>Server</b>")
                parts.extend(dev_lines)
                parts.append("")

        # Tags
        if payload.tags:
            tags_str = " ".join(
                f"<code>#{_escape(k)}:{_escape(v)}</code>"
                for k, v in payload.tags.items()
            )
            parts.append(f"<b>Tags:</b> {tags_str}")
            parts.append("")

        # Metadata
        if payload.metadata:
            meta_str = "\n".join(
                f"  {_escape(str(k))}: {_escape(str(v))}"
                for k, v in list(payload.metadata.items())[:20]
            )
            if len(meta_str) > self.max_metadata:
                meta_str = meta_str[: self.max_metadata] + "\n  ... (truncated)"
            parts.append("<b>Metadata</b>")
            parts.append(f"<pre>{meta_str}</pre>")
            parts.append("")

        # Stacktrace
        if payload.stacktrace:
            trace = payload.stacktrace
            if len(trace) > self.max_stacktrace:
                trace = trace[: self.max_stacktrace] + "\n... (truncated)"
            parts.append("<b>Stacktrace</b>")
            parts.append(f"<pre>{_escape(trace)}</pre>")
            parts.append("")

        # Timestamp & fingerprint
        ts = payload.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
        parts.append(f"<i>{ts}</i>")
        if payload.fingerprint:
            parts.append(f"Fingerprint: <code>{_escape(payload.fingerprint)}</code>")

        message = "\n".join(parts)

        # Telegram message limit is 4096 characters
        if len(message) > 4096:
            message = message[:4080] + "\n\n... (truncated)"

        return message


def _escape(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
