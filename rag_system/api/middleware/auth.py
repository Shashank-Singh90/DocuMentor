"""
Authentication middleware for the API.
Using simple API key auth for now - might switch to JWT later if we need more features.

Created: Nov 2024
Last modified: Nov 18, 2024
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
from rag_system.config.settings import get_settings
from rag_system.core.utils.logger import get_logger
from rag_system.core.constants import ERROR_INVALID_API_KEY

logger = get_logger(__name__)
settings = get_settings()

# Using X-API-Key header - seems to be the standard approach most APIs use
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Check if the API key in the request is valid.
    Returns the key if valid, raises 401 if not.
    """
    # Allow all requests if no API key is configured
    # This is handy for local dev - don't have to mess with auth every time
    if not settings.api_key:
        logger.debug("API key auth is disabled - no key in settings")
        return "anonymous"

    # No key provided in request
    if not api_key:
        logger.warning("Request missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Check if the provided key matches
    if api_key != settings.api_key:
        # Log only first 8 chars for security reasons (don't want full keys in logs)
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("API key verified")
    return api_key


async def optional_verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Optional API key check - doesn't fail if the key is missing or wrong.
    Useful for public endpoints where we want to track authenticated vs anonymous usage.
    """
    if not settings.api_key or not api_key:
        return None

    # Return the key if it's valid, otherwise None
    if api_key == settings.api_key:
        logger.debug("Optional auth - key is valid")
        return api_key

    # Invalid key provided, but we don't fail - just treat as anonymous
    logger.debug("Optional auth - invalid key, treating as anonymous")
    return None
