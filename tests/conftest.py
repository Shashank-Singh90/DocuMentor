"""
Shared pytest fixtures and configuration
"""
import pytest
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_query():
    """Sample query for testing"""
    return "How do I create a FastAPI endpoint?"


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    return [
        {
            "content": "FastAPI is a modern web framework...",
            "metadata": {"source": "fastapi_docs"},
            "score": 0.95
        },
        {
            "content": "To create an endpoint, use @app.get()...",
            "metadata": {"source": "fastapi_tutorial"},
            "score": 0.87
        }
    ]


@pytest.fixture
def sample_api_key():
    """Sample API key for testing (meets minimum length requirement)"""
    return "test-api-key-1234567890abcdef"
