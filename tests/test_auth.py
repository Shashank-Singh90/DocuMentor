"""
Unit tests for authentication middleware
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
from rag_system.api.middleware.auth import verify_api_key, optional_verify_api_key


class TestVerifyAPIKey:
    """Tests for API key verification"""

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_no_api_key_configured(self, mock_settings):
        """Test that missing API key configuration raises error"""
        mock_settings.api_key = None

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("some-key")

        assert exc_info.value.status_code == 500

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_missing_api_key_header(self, mock_settings):
        """Test that missing API key in request is rejected"""
        mock_settings.api_key = "test-key-1234567890"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(None)

        assert exc_info.value.status_code == 401

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_api_key_too_short(self, mock_settings):
        """Test that API keys below minimum length are rejected"""
        mock_settings.api_key = "test-key-1234567890"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("short")

        assert exc_info.value.status_code == 401

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, mock_settings):
        """Test that incorrect API keys are rejected"""
        mock_settings.api_key = "correct-api-key-123456"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key("wrong-api-key-1234567")

        assert exc_info.value.status_code == 401

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_valid_api_key(self, mock_settings):
        """Test that correct API key is accepted"""
        api_key = "correct-api-key-123456"
        mock_settings.api_key = api_key

        result = await verify_api_key(api_key)

        assert result == api_key


class TestOptionalVerifyAPIKey:
    """Tests for optional API key verification"""

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_no_api_key_configured(self, mock_settings):
        """Test that None is returned when no API key is configured"""
        mock_settings.api_key = None

        result = await optional_verify_api_key("some-key")

        assert result is None

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_no_api_key_provided(self, mock_settings):
        """Test that None is returned when no API key is provided"""
        mock_settings.api_key = "test-key-1234567890"

        result = await optional_verify_api_key(None)

        assert result is None

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_valid_api_key(self, mock_settings):
        """Test that correct API key is returned"""
        api_key = "correct-api-key-123456"
        mock_settings.api_key = api_key

        result = await optional_verify_api_key(api_key)

        assert result == api_key

    @patch('rag_system.api.middleware.auth.settings')
    @pytest.mark.asyncio
    async def test_invalid_api_key(self, mock_settings):
        """Test that incorrect API key returns None (not raises)"""
        mock_settings.api_key = "correct-api-key-123456"

        result = await optional_verify_api_key("wrong-api-key-1234567")

        assert result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
