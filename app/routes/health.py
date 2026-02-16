from __future__ import annotations

import logging

from fastapi import APIRouter

from app.core.config import get_settings
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns the health status of the webhook service and Telegram connectivity.",
)
async def health_check() -> dict:
    settings = get_settings()

    # Verify Telegram bot connectivity
    telegram = TelegramService()
    bot_info = await telegram.verify_bot()

    return {
        "status": "healthy" if bot_info else "degraded",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "telegram": {
            "connected": bot_info is not None,
            "bot_username": bot_info.get("username") if bot_info else None,
        },
    }


@router.get(
    "/",
    summary="Root",
    description="Service information.",
)
async def root() -> dict:
    settings = get_settings()
    return {
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
