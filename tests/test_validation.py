"""
Unit tests for input validation functions
"""
import pytest
from fastapi import HTTPException
from rag_system.api.middleware.validation import (
    validate_query,
    validate_search_k,
    validate_temperature,
    validate_max_tokens,
    sanitize_filename
)


class TestQueryValidation:
    """Tests for query validation"""

    def test_valid_query(self):
        """Test that valid queries are accepted"""
        result = validate_query("test query")
        assert result == "test query"

    def test_query_whitespace_normalization(self):
        """Test that excess whitespace is normalized"""
        result = validate_query("test   query   with    spaces")
        assert result == "test query with spaces"

    def test_query_too_short(self):
        """Test that queries below minimum length are rejected"""
        with pytest.raises(HTTPException) as exc_info:
            validate_query("")
        assert exc_info.value.status_code == 400

    def test_query_too_long(self):
        """Test that queries exceeding maximum length are rejected"""
        long_query = "a" * 1001
        with pytest.raises(HTTPException) as exc_info:
            validate_query(long_query)
        assert exc_info.value.status_code == 400


class TestSearchKValidation:
    """Tests for search result count validation"""

    def test_valid_k(self):
        """Test that valid k values are accepted"""
        assert validate_search_k(5) == 5
        assert validate_search_k(1) == 1
        assert validate_search_k(100) == 100

    def test_k_too_small(self):
        """Test that k values below 1 are rejected"""
        with pytest.raises(HTTPException) as exc_info:
            validate_search_k(0)
        assert exc_info.value.status_code == 400

    def test_k_too_large(self):
        """Test that k values exceeding maximum are rejected"""
        with pytest.raises(HTTPException) as exc_info:
            validate_search_k(101)
        assert exc_info.value.status_code == 400


class TestTemperatureValidation:
    """Tests for temperature parameter validation"""

    def test_valid_temperature(self):
        """Test that valid temperature values are accepted"""
        assert validate_temperature(0.0) == 0.0
        assert validate_temperature(0.5) == 0.5
        assert validate_temperature(1.0) == 1.0

    def test_temperature_out_of_range(self):
        """Test that temperature values outside [0,1] are rejected"""
        with pytest.raises(HTTPException):
            validate_temperature(-0.1)

        with pytest.raises(HTTPException):
            validate_temperature(1.1)


class TestMaxTokensValidation:
    """Tests for max_tokens parameter validation"""

    def test_valid_max_tokens(self):
        """Test that valid max_tokens values are accepted"""
        assert validate_max_tokens(100) == 100
        assert validate_max_tokens(1000) == 1000
        assert validate_max_tokens(4000) == 4000

    def test_max_tokens_too_small(self):
        """Test that max_tokens below minimum are rejected"""
        with pytest.raises(HTTPException):
            validate_max_tokens(99)

    def test_max_tokens_too_large(self):
        """Test that max_tokens above maximum are rejected"""
        with pytest.raises(HTTPException):
            validate_max_tokens(4001)


class TestFilenameSanitization:
    """Tests for filename sanitization"""

    def test_simple_filename(self):
        """Test that simple filenames pass through"""
        result = sanitize_filename("test.txt")
        assert result == "test.txt"

    def test_path_traversal_prevention(self):
        """Test that path traversal attempts are blocked"""
        # Using basename extraction should prevent this
        result = sanitize_filename("../../etc/passwd")
        assert result == "passwd"

    def test_url_encoded_traversal_prevention(self):
        """Test that URL-encoded path traversal is blocked"""
        result = sanitize_filename("%2e%2e%2fpasswd")
        assert "../passwd" not in result
        assert result == "passwd"

    def test_dangerous_characters_removed(self):
        """Test that dangerous characters are replaced"""
        result = sanitize_filename("test<>:|?*.txt")
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result
        assert "?" not in result
        assert "*" not in result

    def test_null_byte_removed(self):
        """Test that null bytes are removed"""
        result = sanitize_filename("test\0.txt")
        assert "\0" not in result

    def test_dot_files_rejected(self):
        """Test that hidden files (starting with dot) are rejected"""
        with pytest.raises(HTTPException):
            sanitize_filename(".hidden")

    def test_dot_dot_rejected(self):
        """Test that parent directory reference is rejected"""
        with pytest.raises(HTTPException):
            sanitize_filename("..")

    def test_empty_filename_rejected(self):
        """Test that empty filenames are rejected"""
        with pytest.raises(HTTPException):
            sanitize_filename("")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
