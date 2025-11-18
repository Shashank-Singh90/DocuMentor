"""
Authentication Middleware for DocuMentor API

Implements API key-based authentication for securing API endpoints.
Uses timing-safe comparison to prevent timing attacks.
"""

import secrets
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from typing import Optional
from rag_system.config.settings import get_settings
from rag_system.core.utils.logger import get_logger
from rag_system.core.constants import ERROR_INVALID_API_KEY, MIN_API_KEY_LENGTH

logger = get_logger(__name__)
settings = get_settings()

# API Key header - using X-API-Key since that's pretty standard
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify API key from request header.
    Uses timing-safe comparison to prevent timing attacks.

    Returns:
        The validated API key string

    Raises:
        HTTPException: If authentication fails
    """
    # Check if API key is configured in settings
    if not settings.api_key:
        logger.error("API key authentication required but no key configured in settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication not properly configured",
        )

    # Check if API key is provided
    if not api_key:
        logger.warning("Request rejected: Missing API key")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate API key length
    if len(api_key) < MIN_API_KEY_LENGTH:
        logger.warning(f"Request rejected: API key too short (length: {len(api_key)})")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ERROR_INVALID_API_KEY,
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Verify API key using timing-safe comparison
    if not secrets.compare_digest(api_key, settings.api_key):
        logger.warning("Request rejected: Invalid API key")
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
    For endpoints that are public but we still want to track who's using them
    Uses timing-safe comparison to prevent timing attacks
    """
    if not settings.api_key or not api_key:
        return None

    # Validate API key length
    if len(api_key) < MIN_API_KEY_LENGTH:
        logger.debug("Optional API key authentication failed (key too short), treating as anonymous")
        return None

    # Return the key if it matches using timing-safe comparison, otherwise None
    if secrets.compare_digest(api_key, settings.api_key):
        logger.debug("Optional API key authenticated successfully")
        return api_key

    logger.debug("Optional API key authentication failed, treating as anonymous")
    return None
