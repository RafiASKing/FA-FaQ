"""
Custom exceptions for application-level error handling.
"""

from typing import Optional


class AppError(Exception):
    """Base class for known application errors."""

    def __init__(
        self,
        message: str,
        ref_code: str = "ERR-APP-000",
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.ref_code = ref_code
        self.status_code = status_code


class SearchError(AppError):
    """Raised when search pipeline (embedding/vector/LLM) fails."""

    def __init__(
        self,
        message: str = "Search service unavailable",
        ref_code: str = "ERR-SRCH-001",
        status_code: int = 503,
    ) -> None:
        super().__init__(message=message, ref_code=ref_code, status_code=status_code)


class AuthError(AppError):
    """Raised for authentication or authorization failures."""

    def __init__(
        self,
        message: str = "Unauthorized request",
        ref_code: str = "ERR-AUTH-001",
        status_code: int = 401,
    ) -> None:
        super().__init__(message=message, ref_code=ref_code, status_code=status_code)


class RateLimitError(AppError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Too many requests",
        ref_code: str = "ERR-RATE-001",
        status_code: int = 429,
    ) -> None:
        super().__init__(message=message, ref_code=ref_code, status_code=status_code)
