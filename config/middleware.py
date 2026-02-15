"""
Middleware Setup - Following Siloam convention: config/middleware.py
Handles CORS, rate limiting, and API key authentication.
"""

from fastapi import FastAPI, Security, HTTPException
from fastapi.security import APIKeyHeader
from starlette.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config.settings import settings


# === Rate Limiter ===
limiter = Limiter(key_func=get_remote_address)


# === API Key Auth ===
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Security(_api_key_header)):
    """
    Dependency for API key validation.
    If API_KEY is not configured (empty), all requests pass through.
    If API_KEY is set, requests must include a valid X-API-Key header.
    """
    if not settings.api_key:
        return  # No key configured = auth disabled

    if not api_key or api_key != settings.api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key",
        )


def setup_middleware(app: FastAPI):
    """Configure all middleware for the application."""
    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
