"""
Authentication dependencies.
"""

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader

from config.settings import settings
from core.exceptions import AuthError


_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(_api_key_header)) -> None:
    """
    Validate X-API-Key header against configured APP_API_KEY.
    If API key is not configured, authentication is disabled.
    """
    if not settings.api_key:
        return

    if not api_key or api_key != settings.api_key:
        err = AuthError(message="Invalid or missing API key", ref_code="ERR-AUTH-401")
        raise HTTPException(status_code=err.status_code, detail=f"{err.message} (Ref: {err.ref_code})")
