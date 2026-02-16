import hashlib
import hmac
import secrets

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings

api_key_header = APIKeyHeader(name="X-Webhook-Secret", auto_error=False)


async def verify_webhook_secret(
    api_key: str | None = Security(api_key_header),
) -> str:
    """Verify the webhook secret from the request header."""
    settings = get_settings()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing webhook secret in X-Webhook-Secret header",
        )

    if not hmac.compare_digest(api_key, settings.WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook secret",
        )

    return api_key


def generate_webhook_secret() -> str:
    """Generate a secure random webhook secret."""
    return secrets.token_urlsafe(32)


def generate_error_id() -> str:
    """Generate a unique error ID."""
    return secrets.token_hex(12)
