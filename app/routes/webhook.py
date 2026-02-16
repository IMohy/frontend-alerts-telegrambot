from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import get_settings
from app.core.rate_limiter import RateLimiter
from app.core.security import generate_error_id, verify_webhook_secret
from app.models.error_payload import ErrorPayload, WebhookResponse
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["webhook"])

# Initialize rate limiter
_settings = get_settings()
rate_limiter = RateLimiter(
    max_requests=_settings.RATE_LIMIT_MAX_ERRORS,
    window_seconds=_settings.RATE_LIMIT_WINDOW_SECONDS,
)


@router.post(
    "/error",
    response_model=WebhookResponse,
    status_code=status.HTTP_200_OK,
    summary="Receive error notification",
    description="Receives an error payload and forwards it as a formatted message to Telegram.",
)
async def receive_error(
    payload: ErrorPayload,
    _secret: str = Depends(verify_webhook_secret),
) -> WebhookResponse:
    """Main webhook endpoint: validates, rate-limits, and sends to Telegram."""

    # Rate limiting
    rate_key = payload.fingerprint or "global"
    if not rate_limiter.is_allowed(rate_key):
        remaining = rate_limiter.remaining(rate_key)
        logger.warning("Rate limit exceeded for key=%s", rate_key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "message": "Rate limit exceeded. Too many error reports.",
                "remaining": remaining,
                "retry_after_seconds": rate_limiter.reset_time(rate_key),
            },
        )

    error_id = generate_error_id()
    logger.info(
        "Received error [%s] severity=%s type=%s from=%s",
        error_id,
        payload.severity.value,
        payload.error_type or "unknown",
        payload.app_name or "unknown",
    )

    # Send to Telegram
    telegram = TelegramService()
    sent = await telegram.send_error_notification(payload, error_id)

    if not sent:
        logger.error("Failed to deliver error [%s] to Telegram", error_id)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to deliver notification to Telegram. Check bot configuration.",
        )

    return WebhookResponse(
        success=True,
        message="Error notification delivered successfully",
        error_id=error_id,
    )


@router.post(
    "/test",
    response_model=WebhookResponse,
    summary="Send a test notification",
    description="Sends a test error notification to verify the Telegram integration.",
)
async def test_notification(
    _secret: str = Depends(verify_webhook_secret),
) -> WebhookResponse:
    """Send a test message to verify everything works."""
    test_payload = ErrorPayload(
        error_message="This is a test notification from Jahiz Error Tracker",
        severity="info",
        error_type="TestNotification",
        app_name="Jahiz Error Tracker",
        environment="test",
        timestamp=datetime.utcnow(),
    )

    error_id = generate_error_id()
    telegram = TelegramService()
    sent = await telegram.send_error_notification(test_payload, error_id)

    if not sent:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to send test notification. Verify TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.",
        )

    return WebhookResponse(
        success=True,
        message="Test notification sent successfully! Check your Telegram.",
        error_id=error_id,
    )
