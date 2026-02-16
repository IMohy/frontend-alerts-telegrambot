from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Jahiz Error Tracker"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    # Webhook Security
    WEBHOOK_SECRET: str

    # Rate Limiting
    RATE_LIMIT_MAX_ERRORS: int = 30
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Message Formatting
    MAX_STACKTRACE_LENGTH: int = 2000
    MAX_METADATA_LENGTH: int = 1000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
