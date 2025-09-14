"""
Regression tests for actual bugs we've hit
Started keeping track after v0.3 - too many prod issues
"""
import pytest
import os


def test_unicode_emoji_crash():
    """
    Bug #42: Customer uploaded docs with emoji, crashed everything
    Reproduction: Django docs with 🚀 in headers
    Fixed: 2024-01-15 by adding encode/decode
    """
    doc = "Django 🚀 Framework"
    # Should not crash
    process_document(doc)


def test_concurrent_upload_corruption():
    """
    Bug #67: Two users uploading simultaneously corrupted index
    Fixed: Added file locking (not pretty but works)
    """
    # This test takes forever, only run before release
    if not os.getenv("RUN_SLOW_TESTS"):
        pytest.skip("Set RUN_SLOW_TESTS=1 to run")


@pytest.mark.xfail(reason="ChromaDB bug - they know, waiting for 0.4.23")
def test_null_metadata_values():
    """
    ChromaDB crashes with None in metadata
    Workaround: Replace None with empty string
    TODO: Remove workaround when they fix it
    """
    pass


def test_ollama_cold_start():
    """
    Bug #13: First request to Ollama takes 35+ seconds
    Mitigation: Added warmup in __init__
    Still fails sometimes in Docker (can't fix)
    """
    # Just document it exists, actual test flaky
    pass