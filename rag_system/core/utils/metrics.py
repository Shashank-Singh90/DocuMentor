"""
Metrics and Observability for DocuMentor
Tracks performance, usage, and system health metrics
"""

import time
from typing import Dict, Any, Optional
from contextlib import contextmanager
from prometheus_client import Counter, Histogram, Gauge, Info
from rag_system.core.constants import (
    METRICS_NAMESPACE,
    METRICS_SUBSYSTEM_API,
    METRICS_SUBSYSTEM_RAG,
    METRICS_SUBSYSTEM_LLM,
    LATENCY_BUCKETS,
)
from rag_system.core.utils.logger import get_logger

logger = get_logger(__name__)

# ============================================
# API Metrics
# ============================================

# Request counters
api_requests_total = Counter(
    'requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status'],
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_API
)

api_request_duration = Histogram(
    'request_duration_seconds',
    'API request duration',
    ['endpoint', 'method'],
    buckets=LATENCY_BUCKETS,
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_API
)

# Authentication metrics
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Authentication attempts',
    ['result'],  # success, failure, missing
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_API
)

# Rate limiting metrics
rate_limit_hits = Counter(
    'rate_limit_hits',
    'Rate limit exceeded count',
    ['endpoint'],
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_API
)

# ============================================
# RAG System Metrics
# ============================================

# Vector store metrics
vector_store_searches = Counter(
    'vector_store_searches_total',
    'Total vector store searches',
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

vector_store_search_duration = Histogram(
    'vector_store_search_duration_seconds',
    'Vector store search duration',
    buckets=LATENCY_BUCKETS,
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

vector_store_documents = Gauge(
    'vector_store_documents',
    'Number of documents in vector store',
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

# Document processing metrics
documents_processed = Counter(
    'documents_processed_total',
    'Total documents processed',
    ['file_type', 'status'],
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

document_processing_duration = Histogram(
    'document_processing_duration_seconds',
    'Document processing duration',
    ['file_type'],
    buckets=LATENCY_BUCKETS,
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

# Chunking metrics
chunks_created = Counter(
    'chunks_created_total',
    'Total chunks created',
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

# ============================================
# LLM Metrics
# ============================================

# LLM requests
llm_requests = Counter(
    'requests_total',
    'Total LLM requests',
    ['provider', 'status'],
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_LLM
)

llm_request_duration = Histogram(
    'request_duration_seconds',
    'LLM request duration',
    ['provider'],
    buckets=LATENCY_BUCKETS,
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_LLM
)

llm_tokens_used = Counter(
    'tokens_used_total',
    'Total LLM tokens used',
    ['provider', 'token_type'],  # token_type: prompt, completion
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_LLM
)

# ============================================
# Cache Metrics
# ============================================

cache_hits = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_type'],  # response, embedding
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

cache_misses = Counter(
    'cache_misses_total',
    'Cache misses',
    ['cache_type'],
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

cache_size = Gauge(
    'cache_size',
    'Current cache size',
    ['cache_type'],
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

# ============================================
# Utility Functions
# ============================================

@contextmanager
def track_request_duration(endpoint: str, method: str):
    """
    Context manager to track request duration

    Args:
        endpoint: API endpoint
        method: HTTP method

    Example:
        with track_request_duration('/api/search', 'POST'):
            # ... process request ...
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        api_request_duration.labels(endpoint=endpoint, method=method).observe(duration)


@contextmanager
def track_llm_request(provider: str):
    """
    Context manager to track LLM request

    Args:
        provider: LLM provider name (ollama, openai, gemini)

    Example:
        with track_llm_request('ollama'):
            # ... call LLM ...
    """
    start_time = time.time()
    status = 'success'
    try:
        yield
    except Exception as e:
        status = 'error'
        logger.error(f"LLM request failed: {e}")
        raise
    finally:
        duration = time.time() - start_time
        llm_request_duration.labels(provider=provider).observe(duration)
        llm_requests.labels(provider=provider, status=status).inc()


@contextmanager
def track_vector_search():
    """
    Context manager to track vector store search

    Example:
        with track_vector_search():
            # ... perform search ...
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        vector_store_search_duration.observe(duration)
        vector_store_searches.inc()


def record_api_request(endpoint: str, method: str, status_code: int):
    """
    Record API request

    Args:
        endpoint: API endpoint
        method: HTTP method
        status_code: HTTP status code
    """
    api_requests_total.labels(
        endpoint=endpoint,
        method=method,
        status=str(status_code)
    ).inc()


def record_auth_attempt(result: str):
    """
    Record authentication attempt

    Args:
        result: Authentication result (success, failure, missing)
    """
    auth_attempts_total.labels(result=result).inc()


def record_rate_limit_hit(endpoint: str):
    """
    Record rate limit hit

    Args:
        endpoint: API endpoint
    """
    rate_limit_hits.labels(endpoint=endpoint).inc()
    logger.warning(f"Rate limit exceeded for endpoint: {endpoint}")


def record_cache_hit(cache_type: str):
    """
    Record cache hit

    Args:
        cache_type: Type of cache (response, embedding)
    """
    cache_hits.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
    """
    Record cache miss

    Args:
        cache_type: Type of cache (response, embedding)
    """
    cache_misses.labels(cache_type=cache_type).inc()


def update_cache_size(cache_type: str, size: int):
    """
    Update cache size gauge

    Args:
        cache_type: Type of cache (response, embedding)
        size: Current cache size
    """
    cache_size.labels(cache_type=cache_type).set(size)


def record_document_processed(file_type: str, status: str):
    """
    Record document processing

    Args:
        file_type: File extension/type
        status: Processing status (success, error)
    """
    documents_processed.labels(file_type=file_type, status=status).inc()


def record_llm_tokens(provider: str, prompt_tokens: int, completion_tokens: int):
    """
    Record LLM token usage

    Args:
        provider: LLM provider
        prompt_tokens: Number of prompt tokens
        completion_tokens: Number of completion tokens
    """
    llm_tokens_used.labels(provider=provider, token_type='prompt').inc(prompt_tokens)
    llm_tokens_used.labels(provider=provider, token_type='completion').inc(completion_tokens)


def update_vector_store_size(document_count: int):
    """
    Update vector store document count

    Args:
        document_count: Current number of documents
    """
    vector_store_documents.set(document_count)


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get summary of key metrics

    Returns:
        Dictionary with metric summaries
    """
    # This is a simple summary - for full metrics, use /metrics endpoint
    return {
        "cache_hit_rate": _calculate_cache_hit_rate(),
        "avg_search_duration": "See /metrics endpoint",
        "total_documents": "See /metrics endpoint",
        "total_llm_requests": "See /metrics endpoint",
    }


def _calculate_cache_hit_rate() -> Optional[float]:
    """Calculate cache hit rate"""
    try:
        # This is a simplified calculation
        # In production, you'd query the actual metric values
        return None  # Placeholder
    except Exception:
        return None
