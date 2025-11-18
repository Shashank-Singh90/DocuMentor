# DocuMentor API Documentation

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Endpoints](#endpoints)
- [Request/Response Examples](#requestresponse-examples)
- [Error Handling](#error-handling)
- [Metrics](#metrics)

---

## Overview

**Base URL**: `http://localhost:8100`

**API Version**: 2.0.0

**Content Type**: `application/json`

**Authentication**: API Key (via `X-API-Key` header)

---

## Authentication

### Required Header

```http
X-API-Key: your-api-key-here
```

### Obtaining an API Key

Set the `API_KEY` in your `.env` file:

```bash
API_KEY=your-secure-random-api-key-min-32-chars
```

### Public Endpoints (No Auth Required)

- `GET /`
- `GET /status`
- `GET /metrics`
- `GET /technologies`

### Protected Endpoints (Auth Required)

All `/api/*` endpoints require authentication.

---

## Rate Limiting

Rate limits are enforced per IP address:

| Endpoint Pattern | Limit | Window |
|-----------------|-------|--------|
| `/api/search` | 60 requests | 1 minute |
| `/api/query` | 30 requests | 1 minute |
| `/api/generate-code` | 20 requests | 1 minute |
| `/api/upload` | 10 requests | 1 minute |

### Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1700000000
```

### Rate Limit Exceeded Response

**Status Code**: `429 Too Many Requests`

```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

---

## Endpoints

### 1. Root Endpoint

**GET** `/`

Returns API information.

**Response**:
```json
{
  "message": "DocuMentor API - AI Documentation Assistant",
  "version": "2.0.0",
  "features": [
    "Smart Documentation Search",
    "AI-Powered Code Generation",
    "Technology-Specific Filtering",
    "Dark/Light Mode Support",
    "Real-time Web Search"
  ],
  "docs": "/docs",
  "status": "/status",
  "technologies": "/technologies"
}
```

---

### 2. System Status

**GET** `/status`

Returns system status and capabilities.

**Response**:
```json
{
  "status": "operational",
  "providers": {
    "ollama": true,
    "openai": false,
    "gemini": false
  },
  "document_count": 15420,
  "available_sources": ["fastapi_docs", "python_docs", "langchain_docs"],
  "available_technologies": [
    "Python 3.13.5",
    "FastAPI",
    "Django 5.2",
    "React & Next.js",
    "Node.js",
    "PostgreSQL",
    "MongoDB",
    "TypeScript",
    "LangChain"
  ],
  "supported_formats": ["pdf", "txt", "md", "docx", "csv", "xlsx", "pptx"],
  "system_version": "2.0.0"
}
```

---

### 3. List Technologies

**GET** `/technologies`

Returns available technologies with statistics.

**Response**:
```json
{
  "total_technologies": 9,
  "technologies": [
    {
      "key": "python",
      "name": "Python 3.13.5",
      "available": true,
      "sample_topics": [
        "Python is a high-level programming language...",
        "Python supports multiple programming paradigms..."
      ]
    }
  ]
}
```

---

### 4. Search Documents

**POST** `/api/search`

🔐 **Authentication Required**

🚦 **Rate Limit**: 60/minute

Semantic search across indexed documents.

**Request Body**:
```json
{
  "query": "How to create FastAPI endpoints?",
  "k": 5,
  "technology_filter": "fastapi",
  "source_filter": ["fastapi_docs"]
}
```

**Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `query` | string | ✅ Yes | - | Search query (1-1000 chars) |
| `k` | integer | No | 8 | Number of results (1-100) |
| `technology_filter` | string | No | null | Filter by technology key |
| `source_filter` | array | No | null | Filter by document sources |

**Response**:
```json
{
  "query": "How to create FastAPI endpoints?",
  "results": [
    {
      "content": "To create a FastAPI endpoint, use the @app decorator...",
      "metadata": {
        "source": "fastapi_docs",
        "title": "FastAPI Endpoints",
        "technology": "fastapi",
        "page": 12
      },
      "score": 0.89
    }
  ],
  "count": 5,
  "search_time": 0.045
}
```

---

### 5. Query with RAG

**POST** `/api/query`

🔐 **Authentication Required**

🚦 **Rate Limit**: 30/minute

Ask questions with Retrieval-Augmented Generation.

**Request Body**:
```json
{
  "question": "How do I add authentication to FastAPI?",
  "search_k": 8,
  "enable_web_search": false,
  "response_mode": "smart_answer",
  "technology_filter": "fastapi",
  "temperature": 0.3,
  "max_tokens": 800
}
```

**Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `question` | string | ✅ Yes | - | Question to ask |
| `search_k` | integer | No | 8 | Context documents to retrieve |
| `enable_web_search` | boolean | No | false | Enable web search |
| `response_mode` | string | No | "smart_answer" | Response format |
| `technology_filter` | string | No | null | Filter by technology |
| `temperature` | float | No | 0.3 | LLM temperature (0.0-1.0) |
| `max_tokens` | integer | No | 800 | Max response length (100-4000) |

**Response**:
```json
{
  "question": "How do I add authentication to FastAPI?",
  "answer": "To add authentication to FastAPI, you can use...",
  "sources": [
    {
      "title": "FastAPI Security",
      "content": "FastAPI provides several tools...",
      "source": "fastapi_docs"
    }
  ],
  "provider_used": "ollama",
  "response_time": 2.134,
  "tokens_used": {
    "prompt": 234,
    "completion": 156
  }
}
```

---

### 6. Generate Code

**POST** `/api/generate-code`

🔐 **Authentication Required**

🚦 **Rate Limit**: 20/minute

Generate code with documentation context.

**Request Body**:
```json
{
  "prompt": "Create a FastAPI endpoint with JWT authentication",
  "language": "python",
  "technology": "fastapi",
  "include_context": true,
  "include_comments": true,
  "temperature": 0.2
}
```

**Parameters**:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `prompt` | string | ✅ Yes | - | Code generation prompt |
| `language` | string | No | "python" | Programming language |
| `technology` | string | No | null | Technology context |
| `include_context` | boolean | No | true | Include relevant docs |
| `include_comments` | boolean | No | true | Add code comments |
| `temperature` | float | No | 0.2 | Creativity level |

**Response**:
```json
{
  "prompt": "Create a FastAPI endpoint with JWT authentication",
  "generated_code": "from fastapi import FastAPI, Depends...",
  "language": "python",
  "context_used": [
    {
      "source": "fastapi_docs",
      "title": "Security - First Steps"
    }
  ],
  "explanation": "This code creates a FastAPI endpoint...",
  "generation_time": 3.421
}
```

---

### 7. Upload Document

**POST** `/api/upload`

🔐 **Authentication Required**

🚦 **Rate Limit**: 10/minute

Upload and process a document.

**Request** (multipart/form-data):

```bash
curl -X POST "http://localhost:8100/api/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@documentation.pdf" \
  -F "title=My Documentation" \
  -F "technology=python" \
  -F "description=Python API documentation"
```

**Form Fields**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | ✅ Yes | Document file (max 50MB) |
| `title` | string | No | Document title |
| `technology` | string | No | Associated technology |
| `description` | string | No | Document description |

**Supported Formats**:
- Documents: PDF, DOCX, DOC, TXT, MD, RTF, ODT
- Spreadsheets: XLSX, XLS, CSV
- Presentations: PPTX, PPT

**Response**:
```json
{
  "success": true,
  "filename": "documentation.pdf",
  "chunks_created": 45,
  "processing_time": 1.234,
  "document_id": "doc_abc123",
  "message": "Document processed successfully"
}
```

**Validation**:
- ✅ MIME type detection (content-based)
- ✅ File size limit (50MB)
- ✅ Path traversal prevention
- ✅ Extension whitelist

---

### 8. Metrics Endpoint

**GET** `/metrics`

Returns Prometheus-compatible metrics.

**Response** (text/plain):
```
# HELP documenter_api_requests_total Total API requests
# TYPE documenter_api_requests_total counter
documenter_api_requests_total{endpoint="/api/search",method="POST",status="200"} 1524.0

# HELP documenter_api_request_duration_seconds API request duration
# TYPE documenter_api_request_duration_seconds histogram
documenter_api_request_duration_seconds_bucket{endpoint="/api/search",method="POST",le="0.01"} 234.0
documenter_api_request_duration_seconds_bucket{endpoint="/api/search",method="POST",le="0.05"} 1200.0
documenter_api_request_duration_seconds_bucket{endpoint="/api/search",method="POST",le="0.1"} 1450.0

# HELP documenter_llm_tokens_used_total Total LLM tokens used
# TYPE documenter_llm_tokens_used_total counter
documenter_llm_tokens_used_total{provider="ollama",token_type="prompt"} 125430.0
documenter_llm_tokens_used_total{provider="ollama",token_type="completion"} 87234.0

# HELP documenter_rag_cache_hits_total Cache hits
# TYPE documenter_rag_cache_hits_total counter
documenter_rag_cache_hits_total{cache_type="response"} 432.0

# HELP documenter_rag_vector_store_documents Number of documents in vector store
# TYPE documenter_rag_vector_store_documents gauge
documenter_rag_vector_store_documents 15420.0
```

---

## Request/Response Examples

### Python Example

```python
import requests

API_URL = "http://localhost:8100"
API_KEY = "your-api-key"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Search documents
response = requests.post(
    f"{API_URL}/api/search",
    headers=headers,
    json={
        "query": "FastAPI dependency injection",
        "k": 5,
        "technology_filter": "fastapi"
    }
)

print(response.json())

# Generate code
response = requests.post(
    f"{API_URL}/api/generate-code",
    headers=headers,
    json={
        "prompt": "Create a CRUD endpoint for users",
        "language": "python",
        "technology": "fastapi"
    }
)

print(response.json())
```

### JavaScript Example

```javascript
const API_URL = 'http://localhost:8100';
const API_KEY = 'your-api-key';

const headers = {
  'X-API-Key': API_KEY,
  'Content-Type': 'application/json'
};

// Search documents
fetch(`${API_URL}/api/search`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    query: 'FastAPI dependency injection',
    k: 5,
    technology_filter: 'fastapi'
  })
})
.then(response => response.json())
.then(data => console.log(data));

// Upload file
const formData = new FormData();
formData.append('file', fileInput.files[0]);
formData.append('title', 'My Document');

fetch(`${API_URL}/api/upload`, {
  method: 'POST',
  headers: { 'X-API-Key': API_KEY },
  body: formData
})
.then(response => response.json())
.then(data => console.log(data));
```

### cURL Examples

```bash
# Health check
curl http://localhost:8100/

# Get status
curl http://localhost:8100/status

# Search with authentication
curl -X POST "http://localhost:8100/api/search" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How to use FastAPI?",
    "k": 5
  }'

# Upload document
curl -X POST "http://localhost:8100/api/upload" \
  -H "X-API-Key: your-api-key" \
  -F "file=@document.pdf" \
  -F "title=Documentation" \
  -F "technology=python"

# View metrics
curl http://localhost:8100/metrics
```

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Error Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| **400** | Bad Request | Invalid parameters, validation failed |
| **401** | Unauthorized | Missing or invalid API key |
| **413** | Payload Too Large | File size exceeds 50MB |
| **422** | Unprocessable Entity | Invalid request body format |
| **429** | Too Many Requests | Rate limit exceeded |
| **500** | Internal Server Error | Server-side error |

### Example Error Responses

**Missing API Key** (401):
```json
{
  "detail": "Invalid or missing API key"
}
```

**Invalid Query** (400):
```json
{
  "detail": "Query must be at least 1 characters"
}
```

**Rate Limit Exceeded** (429):
```json
{
  "detail": "Rate limit exceeded. Please try again later."
}
```

**File Too Large** (413):
```json
{
  "detail": "File size exceeds maximum allowed size of 50MB"
}
```

**Invalid File Type** (400):
```json
{
  "detail": "Unsupported file type. Supported: .pdf, .docx, .txt, ..."
}
```

---

## Metrics

### Tracked Metrics

**API Performance**:
- Request count by endpoint, method, status
- Request duration (P50, P95, P99)
- Authentication attempts (success/failure)
- Rate limit hits

**RAG System**:
- Vector store searches
- Search latency
- Documents indexed
- Document processing time

**LLM Usage**:
- Requests by provider (ollama, openai, gemini)
- Token usage (prompt + completion)
- Response time by provider

**Cache Performance**:
- Cache hits/misses (response cache, embedding cache)
- Cache size
- Cache hit rate

### Grafana Queries

**Average Search Latency**:
```promql
rate(documenter_rag_vector_store_search_duration_seconds_sum[5m])
/
rate(documenter_rag_vector_store_searches_total[5m])
```

**Cache Hit Rate**:
```promql
rate(documenter_rag_cache_hits_total[5m])
/
(rate(documenter_rag_cache_hits_total[5m]) + rate(documenter_rag_cache_misses_total[5m]))
```

**API Error Rate**:
```promql
sum(rate(documenter_api_requests_total{status=~"5.."}[5m]))
/
sum(rate(documenter_api_requests_total[5m]))
```

**LLM Token Usage**:
```promql
sum by (provider, token_type) (rate(documenter_llm_tokens_used_total[1h]))
```

---

## Interactive Documentation

When the server is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8100/docs
- **ReDoc**: http://localhost:8100/redoc

These interfaces allow you to:
- ✅ View all endpoints with detailed schemas
- ✅ Try out API calls directly in the browser
- ✅ See request/response examples
- ✅ Test authentication

---

## Versioning

**Current Version**: 2.0.0

**Version Format**: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking API changes
- **MINOR**: New features (backwards compatible)
- **PATCH**: Bug fixes

**Version Header**: All responses include:
```http
X-API-Version: 2.0.0
```

---

## Support

For issues, questions, or feature requests:

- **GitHub Issues**: [Shashank-Singh90/DocuMentor/issues](https://github.com/Shashank-Singh90/DocuMentor/issues)
- **Documentation**: [README.md](README.md)
- **Improvements Guide**: [IMPROVEMENTS.md](IMPROVEMENTS.md)

---

**Last Updated**: November 2025
**API Version**: 2.0.0
