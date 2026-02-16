from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routes import health, webhook

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle events."""
    settings = get_settings()
    logger.info("Starting %s v%s", settings.APP_NAME, settings.APP_VERSION)

    from app.services.telegram_service import TelegramService

    telegram = TelegramService()
    bot_info = await telegram.verify_bot()
    if bot_info:
        logger.info(
            "Telegram bot connected: @%s", bot_info.get("username", "unknown")
        )
    else:
        logger.warning(
            "Could not connect to Telegram bot. Check TELEGRAM_BOT_TOKEN."
        )

    yield

    logger.info("Shutting down %s", settings.APP_NAME)


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "A professional webhook service that receives error notifications "
            "from your applications and instantly delivers them to Telegram "
            "with rich formatting and full context."
        ),
        lifespan=lifespan,
    )

    # CORS (allow all origins for webhook ingestion)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    app.include_router(health.router)
    app.include_router(webhook.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
