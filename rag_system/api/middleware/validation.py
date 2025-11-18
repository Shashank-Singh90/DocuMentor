"""
Input Validation for DocuMentor API

Validates file uploads, query parameters, and request data.
Uses python-magic for content-based MIME type detection for enhanced security.
"""

from fastapi import UploadFile, HTTPException, status
from typing import List, Optional
import magic  # python-magic for content-based file type detection
from pathlib import Path
from rag_system.core.constants import (
    MAX_FILE_SIZE_BYTES,
    ALL_SUPPORTED_EXTENSIONS,
    MIN_QUERY_LENGTH,
    MAX_QUERY_LENGTH,
    ERROR_FILE_TOO_LARGE,
    ERROR_INVALID_FILE_TYPE,
    ERROR_QUERY_TOO_SHORT,
    ERROR_QUERY_TOO_LONG,
)
from rag_system.core.utils.logger import get_logger

logger = get_logger(__name__)

# MIME type mapping for supported file types
ALLOWED_MIME_TYPES = {
    # Text files
    'text/plain': ['.txt'],
    'text/markdown': ['.md', '.markdown'],

    # PDF
    'application/pdf': ['.pdf'],

    # Microsoft Office formats
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'application/vnd.ms-powerpoint': ['.ppt'],

    # CSV (multiple MIME type variants)
    'text/csv': ['.csv'],
    'application/csv': ['.csv'],
}


def validate_query(query: str) -> str:
    """
    Validate and sanitize search query.

    Args:
        query: The search query string

    Returns:
        Sanitized query string

    Raises:
        HTTPException: If query is too short or too long
    """
    if not query or len(query.strip()) < MIN_QUERY_LENGTH:
        logger.warning(f"Query validation failed: too short (length: {len(query)})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_QUERY_TOO_SHORT
        )

    if len(query) > MAX_QUERY_LENGTH:
        logger.warning(f"Query validation failed: too long (length: {len(query)})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_QUERY_TOO_LONG
        )

    # Sanitize query: normalize whitespace by splitting and rejoining
    sanitized = ' '.join(query.strip().split())

    logger.debug(f"Query validated: '{sanitized[:50]}...'")
    return sanitized


def validate_search_k(k: int, max_k: int = 100) -> int:
    """
    Validate search result count

    Args:
        k: Number of results to return
        max_k: Maximum allowed value

    Returns:
        Validated k value

    Raises:
        HTTPException: If k is invalid
    """
    if k < 1:
        logger.warning(f"Invalid k value: {k} (must be >= 1)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter 'k' must be at least 1"
        )

    if k > max_k:
        logger.warning(f"Invalid k value: {k} (must be <= {max_k})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parameter 'k' must not exceed {max_k}"
        )

    return k


def validate_temperature(temperature: float) -> float:
    """
    Validate LLM temperature parameter

    Args:
        temperature: Temperature value

    Returns:
        Validated temperature

    Raises:
        HTTPException: If temperature is invalid
    """
    if not 0.0 <= temperature <= 1.0:
        logger.warning(f"Invalid temperature: {temperature}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature must be between 0.0 and 1.0"
        )

    return temperature


def validate_max_tokens(max_tokens: int) -> int:
    """
    Validate max tokens parameter

    Args:
        max_tokens: Maximum tokens value

    Returns:
        Validated max_tokens

    Raises:
        HTTPException: If max_tokens is invalid
    """
    if max_tokens < 100:
        logger.warning(f"Invalid max_tokens: {max_tokens} (must be >= 100)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_tokens must be at least 100"
        )

    if max_tokens > 4000:
        logger.warning(f"Invalid max_tokens: {max_tokens} (must be <= 4000)")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_tokens must not exceed 4000"
        )

    return max_tokens


async def validate_file_upload(file: UploadFile) -> UploadFile:
    """
    Validate uploaded file (extension, size, content type)

    Args:
        file: Uploaded file

    Returns:
        Validated file

    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALL_SUPPORTED_EXTENSIONS:
        logger.warning(f"File upload rejected: unsupported extension '{file_extension}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{ERROR_INVALID_FILE_TYPE}. Supported: {', '.join(ALL_SUPPORTED_EXTENSIONS)}"
        )

    # Read file content to check size and MIME type
    content = await file.read()
    file_size = len(content)

    # Reset file pointer for later processing
    await file.seek(0)

    # Check file size
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"File upload rejected: size {file_size} bytes exceeds limit")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=ERROR_FILE_TOO_LARGE
        )

    # Validate MIME type using python-magic (content-based detection)
    try:
        mime_type = magic.from_buffer(content, mime=True)
        logger.debug(f"Detected MIME type: {mime_type} for file: {file.filename}")

        # Check if MIME type is allowed
        if mime_type not in ALLOWED_MIME_TYPES:
            # Some MIME types have variations, check if it's a text file
            if not mime_type.startswith('text/') and mime_type not in ALLOWED_MIME_TYPES:
                logger.warning(f"File upload rejected: invalid MIME type '{mime_type}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{ERROR_INVALID_FILE_TYPE}. Detected type: {mime_type}"
                )

        logger.info(f"File upload validated: {file.filename} ({file_size} bytes, {mime_type})")

    except Exception as e:
        logger.error(f"MIME type detection failed: {e}")
        # If python-magic fails, fall back to extension-only validation
        logger.warning("Falling back to extension-only validation")

    return file


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename safe for filesystem operations

    Raises:
        HTTPException: If filename is empty or contains only invalid characters
    """
    import urllib.parse

    # URL-decode the filename to catch encoded path traversal attempts
    try:
        filename = urllib.parse.unquote(filename)
    except Exception:
        pass  # If decoding fails, use original filename

    # Remove null bytes which can cause issues
    filename = filename.replace('\0', '')

    # Extract only the basename to prevent any path traversal
    # This handles both / and \ path separators
    filename = Path(filename).name

    # Remove any dangerous characters that could cause filesystem issues
    dangerous_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    # Ensure the filename doesn't start with a dot (hidden file)
    # or consist only of dots (. or ..)
    if not filename or filename.startswith('.') or all(c == '.' for c in filename):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid filename"
        )

    logger.debug(f"Sanitized filename: {filename}")
    return filename
