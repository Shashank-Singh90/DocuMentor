# DocuMentor

> **AI-Powered Documentation Assistant with Retrieval-Augmented Generation (RAG)**

DocuMentor is an intelligent documentation assistant that helps developers quickly find, understand, and generate code based on comprehensive documentation databases. Built with FastAPI, Streamlit, and ChromaDB, it provides both a modern web interface and production-ready REST API.

## Features

### Core Capabilities

- **Intelligent Documentation Search** - Semantic search across 9+ programming technologies using vector embeddings
- **AI-Powered Code Generation** - Context-aware code generation with technology-specific knowledge
- **Multi-Provider LLM Support** - Flexible integration with Ollama (local), OpenAI, and Google Gemini
- **Real-Time Web Search** - Augment documentation with live web results
- **Modern Web UI** - User-friendly Streamlit interface with dark/light mode
- **Production REST API** - FastAPI backend with authentication and rate limiting
- **Document Processing** - Upload and process 10+ file formats (PDF, DOCX, PPTX, etc.)

### Supported Technologies

- Python 3.13.5
- FastAPI
- Django 5.2
- React & Next.js
- Node.js
- PostgreSQL
- MongoDB
- TypeScript
- LangChain

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama (for local LLM) or OpenAI/Gemini API keys
- 2GB+ RAM for vector database

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/Shashank-Singh90/DocuMentor.git
cd DocuMentor
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your settings (see Configuration section)
```

4. **Start the application**
```bash
# Option 1: Launch complete system (FastAPI + Streamlit)
python launcher.py

# Option 2: Start web UI only
python main.py

# Option 3: Start API server only
python api_server.py
```

5. **Access the application**
- Web UI: http://127.0.0.1:8506
- API Server: http://127.0.0.1:8100
- API Documentation: http://127.0.0.1:8100/docs

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     User Interfaces                          │
│  ┌──────────────────┐              ┌──────────────────────┐ │
│  │  Streamlit UI    │              │    FastAPI REST API  │ │
│  │  (Port 8506)     │              │    (Port 8100)       │ │
│  └────────┬─────────┘              └──────────┬───────────┘ │
└───────────┼──────────────────────────────────┼──────────────┘
            │                                   │
            └───────────────┬───────────────────┘
                           │
            ┌──────────────▼───────────────┐
            │   Core RAG System (Shared)   │
            ├──────────────────────────────┤
            │ • Authentication Middleware  │
            │ • Rate Limiting              │
            │ • Input Validation          │
            │ • Metrics & Monitoring       │
            └──────────────┬───────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
   ┌─────────┐      ┌─────────────┐    ┌──────────┐
   │ Vector  │      │   LLM       │    │   Web    │
   │ Store   │      │ Handler     │    │  Search  │
   │ (Chroma)│      │ (Multi-     │    │          │
   │         │      │  Provider)  │    │          │
   └────┬────┘      └─────────────┘    └──────────┘
        │
   ┌────▼────────────────────────────┐
   │  Document Processing Pipeline   │
   │  • Smart Chunker               │
   │  • Multi-format Processor      │
   │  • Metadata Extraction         │
   └─────────────────────────────────┘
```

### Technology Stack

**Backend**
- FastAPI 0.115.0 - REST API framework
- Uvicorn 0.32.0 - ASGI server
- Streamlit 1.29.0 - Web UI framework

**Vector Database & AI**
- ChromaDB 1.1.0 - Vector database for embeddings
- LangChain 0.3.27 - LLM orchestration
- sentence-transformers 5.1.0 - Embedding model (all-MiniLM-L6-v2)

**LLM Providers**
- Ollama - Local LLM inference (default: gemma2:2b)
- OpenAI - GPT API integration
- Google Gemini - Alternative cloud LLM

**Document Processing**
- pypdf 6.0.0 - PDF processing
- python-docx 1.1.0 - Word documents
- python-pptx 0.6.0 - PowerPoint
- openpyxl 3.1.0 - Excel files
- beautifulsoup4 4.12.0 - HTML parsing

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following settings:

```bash
# Application Settings
APP_NAME=RAG System
APP_VERSION=2.0.0
DEBUG=false
HOST=127.0.0.1
PORT=8501

# Ollama Configuration
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=gemma2:2b  # Options: llama2, mixtral, gemma2:2b
OLLAMA_TIMEOUT=120

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
COLLECTION_NAME=documents
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIMENSION=384

# Chunking Configuration
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CHUNKS_PER_DOC=1000

# Caching
CACHE_DIR=./data/cache
EMBEDDING_CACHE_DIR=./data/cache/embeddings
MAX_CACHE_SIZE=1000
CACHE_TTL=3600
MAX_EMBEDDING_CACHE_SIZE=10000

# Performance
MAX_WORKERS=4
BATCH_SIZE=100
TIMEOUT=30

# File Upload
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=52428800  # 50 MB
ALLOWED_EXTENSIONS=.txt,.md,.pdf,.docx,.doc,.rtf,.csv,.odt,.pptx,.xlsx

# API & Security
API_KEY=  # Optional, recommended for production (min 16 chars)
CORS_ORIGINS=http://localhost:3000,http://localhost:8501,http://127.0.0.1:8501,http://127.0.0.1:8506

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/rag_system.log
LOG_MAX_SIZE=10485760  # 10 MB
LOG_BACKUP_COUNT=5

# External APIs (Optional)
OPENAI_API_KEY=  # For OpenAI provider
GEMINI_API_KEY=  # For Google Gemini provider
FIRECRAWL_API_KEY=  # For web search
FIRECRAWL_API_URL=http://localhost:3002

# LLM Provider Settings
DEFAULT_LLM_PROVIDER=ollama  # Options: ollama, openai, gemini
ENABLE_WEB_SEARCH=true
ENABLE_CODE_GENERATION=true
ENABLE_SOURCE_FILTERING=true
```

### Ollama Setup

1. **Install Ollama**
```bash
# Linux/Mac
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Download from https://ollama.ai/download
```

2. **Pull a model**
```bash
ollama pull gemma2:2b  # Recommended: Fast, 2B parameters
# Or
ollama pull llama2     # Alternative: More capable, slower
```

3. **Verify Ollama is running**
```bash
curl http://localhost:11434/api/version
```

## API Reference

### REST API Endpoints

#### General Endpoints

**Get API Information**
```http
GET /
```

**Check System Status**
```http
GET /status
```
Response:
```json
{
  "status": "operational",
  "version": "2.0.0",
  "llm_providers": ["ollama", "openai", "gemini"],
  "features": {
    "web_search": true,
    "code_generation": true,
    "source_filtering": true
  }
}
```

**Get Prometheus Metrics**
```http
GET /metrics
```

#### Technology Endpoints

**List Available Technologies**
```http
GET /technologies
```

**Get Technology Statistics**
```http
GET /technologies/{technology}/stats
```

#### Q&A Endpoints

**Enhanced Question Answering**
```http
POST /ask/enhanced
Content-Type: application/json

{
  "question": "How do I create a FastAPI endpoint?",
  "search_k": 5,
  "enable_web_search": false,
  "response_mode": "smart",
  "technology_filter": "fastapi",
  "source_filter": "",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

Response:
```json
{
  "answer": "To create a FastAPI endpoint...",
  "sources": [
    {
      "content": "FastAPI endpoint example...",
      "metadata": {
        "source": "fastapi_docs.json",
        "technology": "FastAPI"
      }
    }
  ],
  "response_time": 1.23,
  "provider_used": "ollama",
  "source_count": 3,
  "technology_context": "FastAPI"
}
```

**Code Generation**
```http
POST /generate-code/enhanced
Content-Type: application/json

{
  "prompt": "Create a REST API endpoint for user authentication",
  "language": "python",
  "technology": "fastapi",
  "include_context": true,
  "style": "complete"
}
```

Response:
```json
{
  "code": "from fastapi import FastAPI, HTTPException...",
  "language": "python",
  "technology": "fastapi",
  "style": "complete",
  "context_used": true,
  "provider": "ollama"
}
```

**Technology-Specific Query**
```http
POST /technology-query
Content-Type: application/json

{
  "technology": "django",
  "question": "How do I create a Django model?",
  "mode": "smart"
}
```

#### Document Management

**Upload Document**
```http
POST /upload
Content-Type: multipart/form-data

file: <file>
source: <optional_source_name>
```

Response:
```json
{
  "success": true,
  "chunks_created": 45,
  "file_type": "application/pdf",
  "metadata": {
    "filename": "python_guide.pdf",
    "size": 1048576
  }
}
```

### Rate Limits

- **Search Endpoints**: 60 requests/minute
- **Upload Endpoint**: 10 requests/minute
- **Query Endpoints**: 30 requests/minute
- **Code Generation**: 20 requests/minute

### Authentication

For production deployments, set the `API_KEY` environment variable and include it in requests:

```http
X-API-Key: your-api-key-here
```

## Usage Examples

### Web UI Usage

1. **Ask a Question**
   - Enter your question in the input field
   - Select response mode (Smart Answer / Code Generation / Detailed Sources)
   - Optionally filter by technology
   - Click "Get Smart Answer" or press Enter

2. **Generate Code**
   - Switch to "Code Generation" mode
   - Describe what you want to build
   - Specify the technology/language
   - Click "Generate Code"

3. **Upload Documents**
   - Use the sidebar upload section
   - Drag and drop or browse for files
   - Supported formats: PDF, DOCX, PPTX, XLSX, TXT, MD, etc.
   - Documents are automatically processed and indexed

4. **Customize Settings**
   - Adjust search depth (k parameter)
   - Enable/disable web search
   - Change LLM provider
   - Modify temperature and max tokens
   - Toggle dark/light mode

### Python API Client

```python
import requests

# Base URL
API_URL = "http://127.0.0.1:8100"

# Ask a question
response = requests.post(
    f"{API_URL}/ask/enhanced",
    json={
        "question": "How do I use async/await in Python?",
        "search_k": 5,
        "response_mode": "smart",
        "technology_filter": "python"
    }
)
result = response.json()
print(result["answer"])

# Generate code
response = requests.post(
    f"{API_URL}/generate-code/enhanced",
    json={
        "prompt": "Create a PostgreSQL connection pool",
        "language": "python",
        "technology": "postgresql",
        "style": "complete"
    }
)
code = response.json()["code"]
print(code)

# Upload a document
with open("my_docs.pdf", "rb") as f:
    response = requests.post(
        f"{API_URL}/upload",
        files={"file": f},
        data={"source": "custom_docs"}
    )
print(response.json())
```

### cURL Examples

```bash
# Ask a question
curl -X POST "http://127.0.0.1:8100/ask/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I create a React component?",
    "technology_filter": "react_nextjs",
    "response_mode": "smart"
  }'

# Generate code
curl -X POST "http://127.0.0.1:8100/generate-code/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a FastAPI endpoint with validation",
    "language": "python",
    "technology": "fastapi"
  }'

# Upload document
curl -X POST "http://127.0.0.1:8100/upload" \
  -F "file=@document.pdf" \
  -F "source=my_docs"

# Get system status
curl "http://127.0.0.1:8100/status"
```

## Project Structure

```
DocuMentor/
├── rag_system/                    # Main application package
│   ├── api/                       # REST API layer
│   │   ├── server.py              # FastAPI application
│   │   └── middleware/
│   │       ├── auth.py            # API key authentication
│   │       └── validation.py      # Input validation
│   │
│   ├── web/                       # Web UI layer
│   │   └── app.py                 # Streamlit application
│   │
│   ├── core/                      # Core RAG components
│   │   ├── retrieval/
│   │   │   └── vector_store.py    # ChromaDB vector store
│   │   │
│   │   ├── generation/
│   │   │   └── llm_handler.py     # Multi-provider LLM support
│   │   │
│   │   ├── chunking/
│   │   │   └── chunker.py         # Smart document chunking
│   │   │
│   │   ├── processing/
│   │   │   └── document_processor.py  # Multi-format processing
│   │   │
│   │   ├── search/
│   │   │   └── web_search.py      # Web search integration
│   │   │
│   │   ├── utils/
│   │   │   ├── logger.py          # Logging utility
│   │   │   ├── cache.py           # Response caching
│   │   │   ├── embedding_cache.py # Embedding caching
│   │   │   └── metrics.py         # Prometheus metrics
│   │   │
│   │   └── constants.py           # System constants
│   │
│   └── config/
│       └── settings.py            # Configuration management
│
├── data/                          # Data directory
│   ├── chroma_db/                 # Vector database storage
│   ├── cache/                     # Response and embedding cache
│   ├── uploads/                   # Uploaded documents
│   ├── scraped/                   # Pre-scraped documentation
│   └── preembedded/               # Pre-embedded documents
│
├── logs/                          # Application logs
├── tests/                         # Test suite
│   ├── test_auth.py
│   ├── test_validation.py
│   ├── test_cache.py
│   └── conftest.py
│
├── launcher.py                    # Launch complete system
├── main.py                        # Launch Streamlit UI
├── api_server.py                  # Launch FastAPI server
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
├── pytest.ini                     # Pytest configuration
└── README.md                      # This file
```

## Advanced Features

### Response Modes

**Smart Answer Mode**
- Balanced, practical responses with examples
- Best for general questions and explanations
- Includes code snippets when relevant

**Code Generation Mode**
- Produces complete, working code implementations
- Includes comments and best practices
- Technology-specific optimizations

**Detailed Sources Mode**
- Comprehensive documentation references
- Multiple source citations
- Deep technical details

### Caching System

DocuMentor implements a two-tier caching system for optimal performance:

**Response Cache**
- LRU eviction policy
- SHA256-based key generation
- Persistent JSON storage
- Configurable TTL and max size

**Embedding Cache**
- Prevents recomputation of text embeddings
- NumPy array serialization
- 10,000 entry limit
- Automatic cache warmup

### Performance Optimizations

1. **Batch Processing** - Parallel document chunking with configurable workers
2. **File Locking** - Thread-safe ChromaDB access
3. **Lazy Loading** - Components loaded on demand
4. **Async Operations** - Non-blocking UI operations
5. **Smart Chunking** - Language-aware text splitting
6. **Connection Pooling** - Efficient HTTP client reuse

### Security Features

1. **API Key Authentication** - Timing-safe comparison prevents timing attacks
2. **CORS Configuration** - Configurable allowed origins
3. **Rate Limiting** - Per-endpoint request throttling
4. **File Validation** - MIME type detection and size limits
5. **Input Sanitization** - Query and filename cleaning
6. **Environment Isolation** - Sensitive data in .env files

## Monitoring & Metrics

### Prometheus Metrics

Access metrics at `http://127.0.0.1:8100/metrics`

**Available Metrics:**
- `rag_api_requests_total` - Total API requests by endpoint and status
- `rag_api_request_duration_seconds` - Request duration histogram
- `rag_vector_search_total` - Vector store search counter
- `rag_llm_requests_total` - LLM requests by provider
- `rag_document_chunks_total` - Document processing counter
- `rag_cache_hits_total` / `rag_cache_misses_total` - Cache performance
- `rag_auth_attempts_total` - Authentication attempts
- `rag_rate_limit_hits_total` - Rate limit violations

### Logging

Logs are written to `./logs/rag_system.log` with rotation:
- Max file size: 10 MB
- Backup count: 5 files
- Format: `[TIMESTAMP] [LEVEL] [MODULE] - MESSAGE`

## Troubleshooting

### Common Issues

**Issue: Ollama connection failed**
```
Solution:
1. Verify Ollama is running: curl http://localhost:11434/api/version
2. Check OLLAMA_HOST in .env
3. Ensure the model is pulled: ollama pull gemma2:2b
```

**Issue: ChromaDB database locked**
```
Solution:
1. Check for stale lock files in ./data/chroma_db/
2. Ensure only one instance is running
3. Restart the application
```

**Issue: File upload fails**
```
Solution:
1. Check file size (max 50 MB by default)
2. Verify file type is supported
3. Check MAX_FILE_SIZE in .env
4. Ensure ./data/uploads/ directory exists
```

**Issue: Out of memory errors**
```
Solution:
1. Reduce BATCH_SIZE in .env
2. Lower MAX_CHUNKS_PER_DOC
3. Clear cache: rm -rf ./data/cache/*
4. Use smaller LLM model (gemma2:2b instead of llama2)
```

**Issue: Slow response times**
```
Solution:
1. Enable caching (ENABLE_CACHING=true)
2. Reduce search_k parameter
3. Use local Ollama instead of cloud APIs
4. Increase MAX_WORKERS for parallel processing
5. Check OLLAMA_TIMEOUT setting
```

### Debug Mode

Enable debug logging:
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

View real-time logs:
```bash
tail -f ./logs/rag_system.log
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=rag_system --cov-report=html

# Run only unit tests
pytest -m unit

# Run integration tests
pytest -m integration
```

### Code Style

This project follows PEP 8 style guidelines. Use type hints and docstrings for all functions.

```python
def process_document(
    file_path: str,
    chunk_size: int = 1000
) -> list[dict]:
    """
    Process a document and return chunks with metadata.

    Args:
        file_path: Path to the document file
        chunk_size: Maximum size of each chunk in characters

    Returns:
        List of dictionaries containing chunk text and metadata
    """
    ...
```

### Adding New LLM Providers

1. Extend `LLMHandler` class in `rag_system/core/generation/llm_handler.py`
2. Add provider-specific configuration in `rag_system/config/settings.py`
3. Update provider selection logic in `llm_handler.py`
4. Add tests in `tests/test_llm_handler.py`

### Adding New Document Types

1. Add file extension to `ALLOWED_EXTENSIONS` in settings
2. Implement processor in `rag_system/core/processing/document_processor.py`
3. Update MIME type mapping in `api/middleware/validation.py`
4. Add tests for the new format

## Deployment

### Production Deployment

1. **Set production environment variables**
```bash
DEBUG=false
API_KEY=your-secure-api-key-here
LOG_LEVEL=INFO
```

2. **Use a process manager**
```bash
# Using systemd
sudo systemctl start documentor

# Using PM2
pm2 start launcher.py --name documentor

# Using Docker (see Docker section)
```

3. **Configure reverse proxy (Nginx example)**
```nginx
server {
    listen 80;
    server_name documentor.example.com;

    location / {
        proxy_pass http://127.0.0.1:8506;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    location /api {
        proxy_pass http://127.0.0.1:8100;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

4. **Enable monitoring**
- Configure Prometheus to scrape `/metrics` endpoint
- Set up Grafana dashboards for visualization
- Configure alerting for critical errors

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8100 8506

CMD ["python", "launcher.py"]
```

```bash
# Build image
docker build -t documentor .

# Run container
docker run -d \
  -p 8100:8100 \
  -p 8506:8506 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  --env-file .env \
  documentor
```

## Performance Benchmarks

Based on typical usage patterns:

| Operation | Response Time | Notes |
|-----------|--------------|-------|
| Simple query (cached) | ~100ms | Cache hit |
| Simple query (uncached) | ~2-3s | Ollama gemma2:2b |
| Complex query | ~5-7s | Multiple sources |
| Code generation | ~3-5s | Complete function |
| Document upload (10MB PDF) | ~5-10s | Including chunking |
| Web search query | ~4-6s | With Firecrawl |

Hardware: Intel i5, 16GB RAM, SSD

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure tests pass (`pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **LangChain** - LLM orchestration framework
- **ChromaDB** - Efficient vector database
- **Streamlit** - Beautiful web UI framework
- **FastAPI** - Modern API framework
- **Ollama** - Local LLM inference
- **sentence-transformers** - High-quality embeddings

## Support

- **Issues**: [GitHub Issues](https://github.com/Shashank-Singh90/DocuMentor/issues)
- **Documentation**: This README
- **API Documentation**: http://127.0.0.1:8100/docs (when running)

## Roadmap

- [ ] Multi-user support with authentication
- [ ] Conversation history and context
- [ ] Advanced filtering and search operators
- [ ] Custom model fine-tuning
- [ ] Integration with GitHub, GitLab, Confluence
- [ ] Mobile app
- [ ] Multi-language support for UI
- [ ] Real-time collaboration features

---

**Built with by Shashank Singh** | Version 2.0.0
