"""
Prometheus metrics integration for monitoring the app.
Helps track API usage, LLM costs, performance, etc.

This has been super useful for debugging production issues.
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

# Track all incoming API requests
api_requests_total = Counter(
    'requests_total',
    'Total API requests',
    ['endpoint', 'method', 'status'],
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_API
)

# Request latency - using custom buckets that work well for our use case
api_request_duration = Histogram(
    'request_duration_seconds',
    'API request duration',
    ['endpoint', 'method'],
    buckets=LATENCY_BUCKETS,
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_API
)

# Auth metrics - track success/failures
auth_attempts_total = Counter(
    'auth_attempts_total',
    'Authentication attempts',
    ['result'],  # success, failure, missing
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_API
)

# Rate limiting hits
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

# Vector store search tracking - useful for performance tuning
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

# Keep track of how many docs we have
vector_store_documents = Gauge(
    'vector_store_documents',
    'Number of documents in vector store',
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

# Document processing counters
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

# Chunk creation counter
chunks_created = Counter(
    'chunks_created_total',
    'Total chunks created',
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_RAG
)

# ============================================
# LLM Metrics
# ============================================

# Track LLM API calls - this is important for monitoring costs
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

# TOKEN USAGE - This is the big one since tokens = money
llm_tokens_used = Counter(
    'tokens_used_total',
    'Total LLM tokens used',
    ['provider', 'token_type'],  # token_type: prompt or completion
    namespace=METRICS_NAMESPACE,
    subsystem=METRICS_SUBSYSTEM_LLM
)

# ============================================
# Cache Metrics
# ============================================

cache_hits = Counter(
    'cache_hits_total',
    'Cache hits',
    ['cache_type'],  # response or embedding
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
# Helper Functions
# ============================================

@contextmanager
def track_request_duration(endpoint: str, method: str):
    """
    Track how long API requests take.
    Usage:
        with track_request_duration('/api/search', 'POST'):
            # do stuff
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
    Track LLM requests - duration and success/failure.
    Provider can be 'ollama', 'openai', 'gemini', etc.
    """
    start_time = time.time()
    status = 'success'
    try:
        yield
    except Exception as e:
        status = 'error'
        logger.error(f"LLM call failed: {e}")
        raise
    finally:
        duration = time.time() - start_time
        llm_request_duration.labels(provider=provider).observe(duration)
        llm_requests.labels(provider=provider, status=status).inc()


@contextmanager
def track_vector_search():
    """
    Track vector store search performance.
    Just wrap your search call with this.
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        vector_store_search_duration.observe(duration)
        vector_store_searches.inc()


def record_api_request(endpoint: str, method: str, status_code: int):
    """Log an API request to metrics"""
    api_requests_total.labels(
        endpoint=endpoint,
        method=method,
        status=str(status_code)
    ).inc()


def record_auth_attempt(result: str):
    """Record auth attempt (result can be 'success', 'failure', or 'missing')"""
    auth_attempts_total.labels(result=result).inc()


def record_rate_limit_hit(endpoint: str):
    """Record when someone hits the rate limit"""
    rate_limit_hits.labels(endpoint=endpoint).inc()
    logger.warning(f"Rate limit hit on {endpoint}")


def record_cache_hit(cache_type: str):
    """Track cache hit (cache_type: 'response' or 'embedding')"""
    cache_hits.labels(cache_type=cache_type).inc()


def record_cache_miss(cache_type: str):
    """Track cache miss (cache_type: 'response' or 'embedding')"""
    cache_misses.labels(cache_type=cache_type).inc()


def update_cache_size(cache_type: str, size: int):
    """Update the current size of a cache"""
    cache_size.labels(cache_type=cache_type).set(size)


def record_document_processed(file_type: str, status: str):
    """Record a processed document (status: 'success' or 'error')"""
    documents_processed.labels(file_type=file_type, status=status).inc()


def record_llm_tokens(provider: str, prompt_tokens: int, completion_tokens: int):
    """
    Record token usage - IMPORTANT for cost tracking!
    Provider: ollama, openai, gemini, etc.
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
