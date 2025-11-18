"""
Authentication Middleware for DocuMentor API
Implements API key-based authentication
"""

from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
from rag_system.config.settings import get_settings
from rag_system.core.utils.logger import get_logger
from rag_system.core.constants import ERROR_INVALID_API_KEY

logger = get_logger(__name__)
settings = get_settings()

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The verified API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    # If no API key is configured in settings, allow all requests
    if not settings.api_key:
        logger.debug("API key authentication disabled (no key configured)")
        return "anonymous"

    # Check if API key is provided
    if not api_key:
        logger.warning("Request rejected: Missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key
    if api_key != settings.api_key:
        logger.warning(f"Request rejected: Invalid API key (provided: {api_key[:8]}...)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("API key authenticated successfully")
    return api_key


async def optional_verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Optional API key verification (doesn't fail if missing)
    Used for public endpoints that benefit from auth but don't require it

    Args:
        api_key: API key from X-API-Key header

    Returns:
        The API key if valid, None otherwise
    """
    if not settings.api_key or not api_key:
        return None

    if api_key == settings.api_key:
        logger.debug("Optional API key authenticated successfully")
        return api_key

    logger.debug("Optional API key authentication failed, treating as anonymous")
    return None
