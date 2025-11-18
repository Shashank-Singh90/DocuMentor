"""
Input validation middleware
Handles validation for file uploads, query params, and other request data.

We're using python-magic for actual MIME type detection instead of just
trusting file extensions (because that's a security risk).
"""

from fastapi import UploadFile, HTTPException, status
from typing import List, Optional
import magic  # for content-based file type detection
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

# MIME types we allow for file uploads
# Note: Microsoft's MIME types are absurdly long...
ALLOWED_MIME_TYPES = {
    # Text files
    'text/plain': ['.txt'],
    'text/markdown': ['.md', '.markdown'],

    # PDF
    'application/pdf': ['.pdf'],

    # Microsoft Office (why are these so long??)
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'application/msword': ['.doc'],
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
    'application/vnd.ms-excel': ['.xls'],
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    'application/vnd.ms-powerpoint': ['.ppt'],

    # CSV (different systems use different MIME types for CSV files)
    'text/csv': ['.csv'],
    'application/csv': ['.csv'],
}


def validate_query(query: str) -> str:
    """Validate and sanitize search queries"""
    if not query or len(query.strip()) < MIN_QUERY_LENGTH:
        logger.warning(f"Query too short: {len(query)} chars")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_QUERY_TOO_SHORT
        )

    if len(query) > MAX_QUERY_LENGTH:
        # Seriously, someone tried to paste an entire essay once
        logger.warning(f"Query too long: {len(query)} chars")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ERROR_QUERY_TOO_LONG
        )

    # Clean up the query - remove weird whitespace/control chars
    # The split/join trick normalizes all whitespace
    sanitized = ' '.join(query.strip().split())

    logger.debug(f"Query OK: '{sanitized[:50]}...'")
    return sanitized


def validate_search_k(k: int, max_k: int = 100) -> int:
    """Validate the number of search results requested"""
    if k < 1:
        logger.warning(f"k too small: {k}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Parameter 'k' must be at least 1"
        )

    if k > max_k:
        logger.warning(f"k too large: {k} (max is {max_k})")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parameter 'k' must not exceed {max_k}"
        )

    return k


def validate_temperature(temperature: float) -> float:
    """Check if temperature parameter is in valid range (0.0 to 1.0)"""
    if not 0.0 <= temperature <= 1.0:
        logger.warning(f"Temperature out of range: {temperature}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Temperature must be between 0.0 and 1.0"
        )

    return temperature


def validate_max_tokens(max_tokens: int) -> int:
    """Validate max_tokens parameter - keep it reasonable"""
    # Min of 100 seems fair - anything less is too short to be useful
    if max_tokens < 100:
        logger.warning(f"max_tokens too small: {max_tokens}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_tokens must be at least 100"
        )

    # Cap at 4000 to avoid huge costs
    if max_tokens > 4000:
        logger.warning(f"max_tokens too large: {max_tokens}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="max_tokens must not exceed 4000"
        )

    return max_tokens


async def validate_file_upload(file: UploadFile) -> UploadFile:
    """
    Validate uploaded files - check extension, size, and actual content type.
    Returns the file if valid, raises 400/413 if not.
    """
    # First check the extension
    file_extension = Path(file.filename).suffix.lower()
    if file_extension not in ALL_SUPPORTED_EXTENSIONS:
        logger.warning(f"Rejected file with bad extension: '{file_extension}'")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{ERROR_INVALID_FILE_TYPE}. Supported: {', '.join(ALL_SUPPORTED_EXTENSIONS)}"
        )

    # Read the file to check size and MIME type
    content = await file.read()
    file_size = len(content)

    # IMPORTANT: Reset file pointer so it can be read again later
    await file.seek(0)

    # Check size limits
    if file_size > MAX_FILE_SIZE_BYTES:
        logger.warning(f"File too large: {file_size} bytes")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=ERROR_FILE_TOO_LARGE
        )

    # Use python-magic to detect actual MIME type (more secure than trusting extensions)
    try:
        mime_type = magic.from_buffer(content, mime=True)
        logger.debug(f"MIME type: {mime_type} for {file.filename}")

        # Check if the MIME type is in our allowed list
        if mime_type not in ALLOWED_MIME_TYPES:
            # Some text files come through with weird MIME types, so allow text/*
            if not mime_type.startswith('text/') and mime_type not in ALLOWED_MIME_TYPES:
                logger.warning(f"Bad MIME type: '{mime_type}'")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"{ERROR_INVALID_FILE_TYPE}. Detected type: {mime_type}"
                )

        logger.info(f"File OK: {file.filename} ({file_size} bytes, {mime_type})")

    except Exception as e:
        # python-magic can be flaky sometimes
        logger.error(f"MIME detection error: {e}")
        logger.warning("Falling back to extension check only")

    return file


def sanitize_filename(filename: str) -> str:
    """Clean up filenames to prevent path traversal and other nastiness"""
    # Strip out any path components (someone could try ../../../etc/passwd)
    filename = Path(filename).name
    filename = filename.replace('..', '')

    # Replace dangerous chars that could cause issues
    # These can mess with filesystems or cause security problems
    dangerous_chars = ['<', '>', ':', '"', '|', '?', '*', '\0']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')

    logger.debug(f"Sanitized: {filename}")
    return filename
