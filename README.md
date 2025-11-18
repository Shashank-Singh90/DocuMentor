# DocuMentor

> An intelligent RAG-powered documentation assistant for developers

DocuMentor is a production-ready Retrieval-Augmented Generation (RAG) system that transforms how developers interact with technical documentation. Built with Python, it combines vector search, multi-provider LLM support, and intelligent document processing to deliver accurate, context-aware answers from comprehensive technical documentation.

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Supported Technologies](#supported-technologies)
- [Project Structure](#project-structure)
- [Development](#development)
- [Performance](#performance)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Capabilities

- **Semantic Search**: Vector-based similarity search powered by ChromaDB with 384-dimensional embeddings
- **Multi-LLM Support**: Ollama (local), OpenAI GPT, and Google Gemini with automatic fallback
- **Smart Code Generation**: Technology-aware code generation with context from documentation
- **Web Search Integration**: Real-time information retrieval via DuckDuckGo and Firecrawl
- **Multi-Format Documents**: Process PDF, DOCX, XLSX, PPTX, TXT, MD, CSV, and more
- **Technology Filtering**: Filter queries by framework (Python, Django, FastAPI, React, etc.)

### Production Features

- **API Key Authentication**: Secure endpoints with timing-safe key comparison
- **Rate Limiting**: Configurable per-endpoint rate limits to prevent abuse
- **Prometheus Metrics**: Complete observability with `/metrics` endpoint
- **Response Caching**: Two-tier caching (embeddings + responses) for 95% faster queries
- **Parallel Processing**: ThreadPoolExecutor-based concurrent document processing
- **CORS Configuration**: Environment-based CORS setup for flexible deployment
- **Structured Logging**: Rich console output with configurable log levels
- **Graceful Degradation**: Automatic fallback mechanisms when services are unavailable

### User Interfaces

- **Streamlit Web UI**: Modern, responsive interface with dark/light mode
- **REST API**: FastAPI-powered API with automatic OpenAPI documentation
- **Dual Launcher**: Run both interfaces simultaneously with health monitoring

## Quick Start

```bash
# Clone the repository
git clone https://github.com/Shashank-Singh90/DocuMentor.git
cd DocuMentor

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings (API keys, ports, etc.)

# Launch the system
python launcher.py
```

Access the interfaces:
- **Web UI**: http://localhost:8506
- **API Docs**: http://localhost:8100/docs
- **Metrics**: http://localhost:8100/metrics

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Interfaces                        │
│  ┌──────────────────┐         ┌──────────────────┐      │
│  │  Streamlit Web   │         │   FastAPI REST   │      │
│  │   Port: 8506     │         │   Port: 8100     │      │
│  └────────┬─────────┘         └────────┬─────────┘      │
└───────────┼──────────────────────────────┼──────────────┘
            │                              │
            └──────────────┬───────────────┘
                           ▼
            ┌──────────────────────────────┐
            │       Core RAG System         │
            ├──────────────────────────────┤
            │ • Smart Chunker               │
            │ • Vector Store (ChromaDB)     │
            │ • LLM Handler (Multi-provider)│
            │ • Document Processor          │
            │ • Web Search Provider         │
            │ • Cache Layer (2-tier)        │
            └──────────────┬───────────────┘
                           │
            ┌──────────────┴────────────────┐
            ▼                               ▼
    ┌───────────────┐           ┌───────────────────┐
    │   ChromaDB    │           │  External Services │
    │  Vector DB    │           ├───────────────────┤
    │  (Persistent) │           │ • Ollama (local)  │
    └───────────────┘           │ • OpenAI API      │
                                │ • Google Gemini   │
                                │ • DuckDuckGo      │
                                │ • Firecrawl       │
                                └───────────────────┘
```

### Design Patterns

- **Repository Pattern**: Abstracted vector store operations
- **Strategy Pattern**: Pluggable LLM providers
- **Factory Pattern**: Document processor for multiple formats
- **Middleware Pattern**: Authentication and validation layers
- **Observer Pattern**: Prometheus metrics collection

## Technology Stack

### Backend Framework
- **Python 3.13.5**: Core language
- **FastAPI 0.115.0**: High-performance async API framework
- **Uvicorn 0.32.0**: ASGI server
- **Pydantic 2.11.0**: Data validation and settings management

### Vector & Embeddings
- **ChromaDB 1.1.0**: Vector database with persistence
- **Sentence-Transformers 5.1.0**: Embedding generation
- **Model**: all-MiniLM-L6-v2 (384 dimensions, optimized for speed)

### AI & LLM
- **LangChain 0.3.27**: RAG framework and document processing
- **Transformers 4.56.0**: Model support infrastructure
- **OpenAI 1.0.0**: GPT-3.5-turbo integration
- **Google Generative AI 0.3.0**: Gemini Pro integration

### Document Processing
- **pypdf 6.0.0**: PDF text extraction
- **python-docx 1.1.0**: Microsoft Word documents
- **python-pptx 0.6.0**: PowerPoint presentations
- **openpyxl 3.1.0**: Excel spreadsheets
- **pandas 2.3.0**: Data manipulation and CSV processing
- **BeautifulSoup 4.12.0**: HTML/XML parsing

### Frontend
- **Streamlit 1.29.0**: Interactive web interface with real-time updates

### Monitoring & Performance
- **Prometheus-client 0.20.0**: Metrics collection and exposure
- **slowapi 0.1.9**: Rate limiting
- **filelock 3.13.0**: Concurrent access control
- **Rich 13.9.0**: Enhanced terminal output

## Installation

### Prerequisites

- **Python 3.11+** (Python 3.13.5 recommended)
- **4GB RAM minimum** (8GB recommended)
- **2GB disk space** (for vector database and cache)
- **Ollama** (optional, for local LLM - recommended for privacy)

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shashank-Singh90/DocuMentor.git
   cd DocuMentor
   ```

2. **Create virtual environment** (recommended)
   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama** (optional but recommended)
   ```bash
   # Visit https://ollama.ai for installation instructions
   # After installation, pull a model:
   ollama pull gemma2:2b
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure:
   - LLM provider settings (Ollama/OpenAI/Gemini)
   - API keys (if using cloud providers)
   - Server ports and host
   - Optional: rate limits, cache settings

6. **Verify installation**
   ```bash
   python tests.py
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Application Settings
APP_NAME=DocuMentor
DEBUG=false
HOST=127.0.0.1
PORT=8501

# LLM Configuration
DEFAULT_LLM_PROVIDER=ollama  # Options: ollama, openai, gemini
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=gemma2:2b
OLLAMA_TIMEOUT=120

# API Keys (Optional - only if using cloud providers)
OPENAI_API_KEY=sk-your-openai-key-here
GEMINI_API_KEY=your-gemini-api-key-here

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
COLLECTION_NAME=documents
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Chunking Strategy
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
MAX_CHUNKS_PER_DOC=1000

# Caching
CACHE_DIR=./data/cache
EMBEDDING_CACHE_DIR=./data/cache/embeddings
MAX_CACHE_SIZE=1000
CACHE_TTL=3600

# Security
API_KEY=your-secure-api-key-min-16-chars  # Optional, leave empty to disable
CORS_ORIGINS=http://localhost:3000,http://localhost:8506

# Rate Limiting (requests per minute)
RATE_LIMIT_SEARCH=60
RATE_LIMIT_UPLOAD=10
RATE_LIMIT_QUERY=30
RATE_LIMIT_GENERATION=20

# File Upload
UPLOAD_DIR=./data/uploads
MAX_FILE_SIZE=52428800  # 50MB in bytes

# Web Search
ENABLE_WEB_SEARCH=true
FIRECRAWL_API_KEY=  # Optional, for enhanced web search

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

### Configuration Profiles

**Development Mode**:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
ENABLE_WEB_SEARCH=false
```

**Production Mode**:
```bash
DEBUG=false
LOG_LEVEL=INFO
API_KEY=your-production-api-key
RATE_LIMIT_SEARCH=30  # Stricter limits
```

**Offline Mode**:
```bash
DEFAULT_LLM_PROVIDER=ollama
ENABLE_WEB_SEARCH=false
# No API keys required
```

## Usage

### Launch Options

**Option 1: Complete System** (Recommended)
```bash
python launcher.py
```
Launches both Web UI (port 8506) and API (port 8100) with health monitoring.

**Option 2: Web UI Only**
```bash
python main.py --port 8506
```

**Option 3: API Only**
```bash
python api_server.py --port 8100 --host 127.0.0.1
```

### Web Interface

Navigate to `http://localhost:8506` after launching.

**Features**:
- **Search Bar**: Enter natural language questions
- **Technology Filter**: Select specific framework (Python, Django, FastAPI, etc.)
- **Response Mode**:
  - **Smart Answer**: Balanced, comprehensive responses
  - **Code Generation**: Working code implementations with examples
  - **Detailed Sources**: In-depth explanations with documentation references
- **Document Upload**: Drag-and-drop or browse to add custom documentation
- **Theme Toggle**: Switch between dark and light modes
- **Chat History**: View previous queries and responses

### API Usage

**Example 1: Ask a Question**
```bash
curl -X POST http://localhost:8100/ask/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I use FastAPI dependency injection?",
    "technology_filter": "fastapi",
    "response_mode": "smart_answer",
    "search_k": 8
  }'
```

**Example 2: Generate Code**
```bash
curl -X POST http://localhost:8100/generate-code/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a REST API endpoint with authentication",
    "language": "python",
    "technology": "fastapi",
    "style": "complete_implementation"
  }'
```

**Example 3: Upload Document**
```bash
curl -X POST http://localhost:8100/upload \
  -F "file=@/path/to/document.pdf" \
  -F "technology=python"
```

**Example 4: Technology-Specific Query**
```bash
curl -X POST http://localhost:8100/technology-query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "database models and migrations",
    "technology": "django",
    "search_k": 5
  }'
```

**Example 5: Check System Status**
```bash
curl http://localhost:8100/status
```

### Python SDK Usage

```python
from rag_system.core.retrieval import VectorStore
from rag_system.core.generation import LLMHandler
from rag_system.config import Settings

# Initialize components
settings = Settings()
vector_store = VectorStore()
llm_handler = LLMHandler()

# Search documentation
results = vector_store.search(
    query="FastAPI routing",
    k=5,
    technology_filter="fastapi"
)

# Generate answer
answer = llm_handler.generate_answer(
    question="How do I create API routes?",
    context=results
)

print(answer)
```

## API Reference

### Core Endpoints

#### `GET /`
Get API information and version.

#### `GET /status`
System health check with capabilities.

**Response**:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "components": {
    "vector_store": "operational",
    "llm_providers": ["ollama", "openai", "gemini"],
    "cache": "enabled",
    "web_search": "enabled"
  },
  "statistics": {
    "total_documents": 270,
    "total_chunks": 1500,
    "cache_hit_rate": 0.87
  }
}
```

#### `GET /technologies`
List all available technology filters.

**Response**:
```json
{
  "technologies": [
    "python",
    "django",
    "fastapi",
    "react",
    "nextjs",
    "nodejs",
    "typescript",
    "postgresql",
    "mongodb",
    "langchain"
  ]
}
```

#### `GET /metrics`
Prometheus metrics endpoint.

### Query Endpoints

#### `POST /ask/enhanced`
Enhanced question-answering with filtering.

**Request Body**:
```json
{
  "question": "string (required)",
  "technology_filter": "string (optional)",
  "response_mode": "smart_answer | code_generation | detailed_sources",
  "search_k": "integer (default: 8)",
  "enable_web_search": "boolean (default: false)"
}
```

**Response**:
```json
{
  "answer": "string",
  "sources": [
    {
      "content": "string",
      "metadata": {
        "source": "string",
        "technology": "string",
        "chunk_id": "integer"
      },
      "similarity_score": "float"
    }
  ],
  "metadata": {
    "llm_provider": "string",
    "response_time": "float",
    "cache_hit": "boolean"
  }
}
```

#### `POST /generate-code/enhanced`
Technology-aware code generation.

**Request Body**:
```json
{
  "prompt": "string (required)",
  "language": "string (required)",
  "technology": "string (optional)",
  "style": "complete_implementation | snippet | explanation",
  "include_comments": "boolean (default: true)"
}
```

#### `POST /technology-query`
Technology-specific filtered queries.

**Request Body**:
```json
{
  "query": "string (required)",
  "technology": "string (required)",
  "search_k": "integer (default: 5)"
}
```

### Document Management

#### `POST /upload`
Upload and process documents.

**Request**: multipart/form-data
- `file`: File to upload (PDF, DOCX, TXT, etc.)
- `technology`: Optional technology tag

**Response**:
```json
{
  "success": true,
  "filename": "string",
  "chunks_created": "integer",
  "technology": "string",
  "processing_time": "float"
}
```

### Rate Limits

| Endpoint | Default Limit |
|----------|---------------|
| `/ask/*` | 30/minute |
| `/generate-code/*` | 20/minute |
| `/upload` | 10/minute |
| `/technology-query` | 30/minute |
| Other endpoints | 60/minute |

Configure limits via environment variables: `RATE_LIMIT_QUERY`, `RATE_LIMIT_GENERATION`, `RATE_LIMIT_UPLOAD`, `RATE_LIMIT_SEARCH`

## Supported Technologies

DocuMentor includes pre-embedded documentation for:

| Technology | Coverage | Size |
|------------|----------|------|
| **Python 3.13.5** | Language fundamentals, stdlib, data types | 11KB + 3.0MB |
| **Django 5.2** | Models, views, templates, ORM | 34KB + 1.1MB |
| **FastAPI** | Routing, async, Pydantic, dependencies | 16KB |
| **React & Next.js** | Components, hooks, SSR, routing | 27KB + 225KB |
| **Node.js** | Event loop, modules, streams, async | 26KB |
| **TypeScript** | Types, interfaces, generics, decorators | 28KB |
| **PostgreSQL** | SQL, queries, indexes, optimization | 22KB + 512KB |
| **MongoDB** | NoSQL, aggregation, indexing, sharding | 23KB |
| **LangChain** | RAG, chains, agents, tools | 39KB |

**Total**: ~224KB pre-embedded + ~4.8MB scraped documentation

## Project Structure

```
DocuMentor/
├── launcher.py                  # System launcher (both UI + API)
├── main.py                      # Streamlit web interface entry
├── api_server.py                # FastAPI REST API entry
├── tests.py                     # Comprehensive test suite
├── requirements.txt             # Python dependencies (56 packages)
├── .env.example                 # Environment configuration template
├── LICENSE                      # MIT License
│
├── rag_system/                  # Core RAG system package
│   ├── __init__.py
│   │
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   └── settings.py          # Pydantic settings (152 lines)
│   │
│   ├── core/                    # Core RAG components
│   │   ├── __init__.py
│   │   ├── constants.py         # System constants (149 lines)
│   │   │
│   │   ├── chunking/            # Document chunking
│   │   │   ├── __init__.py
│   │   │   └── chunker.py       # Smart chunking algorithm (376 lines)
│   │   │
│   │   ├── retrieval/           # Vector search
│   │   │   ├── __init__.py
│   │   │   └── vector_store.py  # ChromaDB interface (359 lines)
│   │   │
│   │   ├── generation/          # LLM integration
│   │   │   ├── __init__.py
│   │   │   └── llm_handler.py   # Multi-provider handler (311 lines)
│   │   │
│   │   ├── processing/          # Document processing
│   │   │   ├── __init__.py
│   │   │   └── document_processor.py  # Multi-format support (451 lines)
│   │   │
│   │   ├── search/              # Web search
│   │   │   ├── __init__.py
│   │   │   └── web_search.py    # DuckDuckGo/Firecrawl (425 lines)
│   │   │
│   │   └── utils/               # Utilities
│   │       ├── __init__.py
│   │       ├── logger.py        # Structured logging (36 lines)
│   │       ├── cache.py         # Response cache (177 lines)
│   │       ├── embedding_cache.py  # Embedding cache
│   │       └── metrics.py       # Prometheus metrics (368 lines)
│   │
│   ├── api/                     # FastAPI REST API
│   │   ├── __init__.py
│   │   ├── server.py            # API routes & logic (541 lines)
│   │   │
│   │   └── middleware/          # API middleware
│   │       ├── __init__.py
│   │       ├── auth.py          # API key authentication (85 lines)
│   │       └── validation.py    # Input validation
│   │
│   └── web/                     # Streamlit web interface
│       ├── __init__.py
│       └── app.py               # Web UI implementation (1013 lines)
│
└── data/                        # Data storage (gitignored)
    ├── preembedded/             # Pre-embedded documentation
    │   ├── python_comprehensive.txt
    │   ├── django_comprehensive.txt
    │   ├── fastapi_comprehensive.txt
    │   ├── react_nextjs_comprehensive.txt
    │   ├── nodejs_comprehensive.txt
    │   ├── typescript_comprehensive.txt
    │   ├── postgresql_comprehensive.txt
    │   ├── mongodb_comprehensive.txt
    │   └── langchain_comprehensive.txt
    │
    ├── scraped/                 # Scraped documentation (JSON)
    │   ├── python_docs.json
    │   ├── django_docs.json
    │   └── ...
    │
    ├── chroma_db/              # Vector database storage
    ├── cache/                  # Response & embedding cache
    └── uploads/                # User-uploaded documents
```

**Code Statistics**:
- **Total Files**: 31 Python files
- **Lines of Code**: ~5,565 lines
- **Documentation**: ~224KB pre-embedded + ~4.8MB scraped

## Development

### Setting Up Development Environment

```bash
# Clone and setup
git clone https://github.com/Shashank-Singh90/DocuMentor.git
cd DocuMentor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install in development mode
pip install -r requirements.txt

# Enable debug mode
echo "DEBUG=true" >> .env
echo "LOG_LEVEL=DEBUG" >> .env

# Run tests
python tests.py
```

### Running Tests

```bash
# Run all tests
python tests.py

# Test specific component
python -c "from rag_system.core import VectorStore; vs = VectorStore(); print('Vector store OK')"

# API health check
curl http://127.0.0.1:8100/status
```

### Adding New Features

**1. Add a New LLM Provider**

Edit `rag_system/core/generation/llm_handler.py`:
```python
class NewProviderHandler:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def generate_answer(self, question: str, context: str) -> str:
        # Implementation
        pass

    def generate_code(self, prompt: str, language: str) -> str:
        # Implementation
        pass
```

Update `LLMHandler.get_available_providers()` to include new provider.

**2. Add Document Format Support**

Edit `rag_system/core/processing/document_processor.py`:
```python
def process_new_format(self, file_path: str) -> List[Dict]:
    """Process new document format"""
    # Implementation
    pass
```

Add to `SUPPORTED_FORMATS` and routing logic.

**3. Add API Endpoint**

Edit `rag_system/api/server.py`:
```python
@app.post("/new-endpoint")
async def new_endpoint(request: RequestModel):
    """New endpoint documentation"""
    # Implementation
    pass
```

### Code Style Guidelines

- **PEP 8**: Follow Python style guide
- **Type Hints**: Use typing annotations
- **Docstrings**: Document all functions and classes
- **Error Handling**: Use try-except with specific exceptions
- **Logging**: Use structured logging for important events
- **Comments**: Explain "why", not "what"

## Performance

### Optimization Features

**1. Two-Tier Caching**
- **Embedding Cache**: 10,000 entry capacity, disk-persistent
- **Response Cache**: 1,000 entry LRU cache, in-memory
- **Impact**: 95% faster for repeated queries

**2. Parallel Processing**
- ThreadPoolExecutor for document chunking
- Concurrent embedding generation
- Batch processing with optimal sizing

**3. Smart Chunking**
- Context-aware splitting (1000 chars, 200 overlap)
- Code block preservation
- Markdown structure awareness

**4. Vector Search Optimization**
- Similarity threshold filtering
- Technology-specific metadata filtering
- Efficient ChromaDB persistence

### Benchmarks

Typical performance on standard hardware (8GB RAM, i5 processor):

| Operation | Time | Cache Hit |
|-----------|------|-----------|
| Query (first time) | 800-1200ms | N/A |
| Query (cached) | 50-100ms | Yes |
| Document upload (PDF, 10 pages) | 2-3s | N/A |
| Embedding generation (1000 chars) | 100-150ms | N/A |
| Code generation | 3-5s | Varies |

### Scaling Considerations

- **Vector Database**: ChromaDB handles millions of documents
- **Concurrent Users**: FastAPI supports hundreds of concurrent connections
- **Memory**: ~500MB base + ~1GB per 100K documents
- **Disk**: ~100MB per 50K documents in vector DB

## Testing

### Test Suite

Run comprehensive tests:
```bash
python tests.py
```

**Test Coverage**:
1. **System Imports**: Verify all modules load correctly
2. **Configuration**: Validate settings and environment
3. **Vector Store**: Test search, insertion, retrieval
4. **Document Processing**: Test all supported formats
5. **LLM Providers**: Check connectivity and generation
6. **API Server**: Test all endpoints
7. **Performance**: Benchmark critical operations

### Manual Testing

**Test Web Interface**:
```bash
python main.py --port 8506
# Visit http://localhost:8506
# Try: "How do I use FastAPI dependencies?"
```

**Test API**:
```bash
python api_server.py --port 8100
# Visit http://localhost:8100/docs
# Try example requests from interactive docs
```

**Test Document Upload**:
```bash
# Via API
curl -X POST http://localhost:8100/upload \
  -F "file=@test.pdf" \
  -F "technology=python"

# Via Web UI
# Drag and drop a document in the sidebar
```

### Debugging

Enable debug mode:
```bash
# In .env
DEBUG=true
LOG_LEVEL=DEBUG
```

Check logs:
```bash
# Logs are printed to console with timestamps
# Look for ERROR or WARNING messages
```

Common issues:
- **ChromaDB locked**: Remove `data/chroma_db/*.lock` files
- **Ollama not responding**: Check `ollama serve` is running
- **Import errors**: Reinstall dependencies `pip install -r requirements.txt`
- **Port in use**: Change ports in `.env` or kill process

## Contributing

Contributions are welcome! Please follow these guidelines:

### How to Contribute

1. **Fork the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/DocuMentor.git
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new features
   - Update documentation

4. **Test your changes**
   ```bash
   python tests.py
   ```

5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```

6. **Push to your fork**
   ```bash
   git push origin feature/amazing-feature
   ```

7. **Open a Pull Request**
   - Describe your changes
   - Link any related issues
   - Wait for review

### Areas for Contribution

- **New LLM providers**: Add support for Claude, Llama, etc.
- **Document formats**: Add support for more file types
- **UI improvements**: Enhance the Streamlit interface
- **Performance**: Optimize caching and search
- **Documentation**: Improve guides and examples
- **Tests**: Increase test coverage
- **Integrations**: Add webhooks, notifications, etc.

### Code Review Process

1. Automated tests must pass
2. Code must follow style guidelines
3. Documentation must be updated
4. At least one maintainer approval required

## License

MIT License

Copyright (c) 2025 Shashank-Singh90

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

## Acknowledgments

- **ChromaDB**: Vector database infrastructure
- **LangChain**: RAG framework and document processing
- **Sentence Transformers**: Efficient embedding models
- **FastAPI**: Modern, high-performance API framework
- **Streamlit**: Rapid web interface development
- **Ollama**: Local LLM infrastructure

## Support & Contact

- **Issues**: [GitHub Issues](https://github.com/Shashank-Singh90/DocuMentor/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Shashank-Singh90/DocuMentor/discussions)
- **Documentation**: [API Docs](http://localhost:8100/docs) (when running)

## Roadmap

### Current Version: 2.0.0

### Planned Features
- [ ] Claude AI integration
- [ ] Streaming responses for long answers
- [ ] Multi-language UI support
- [ ] User authentication and sessions
- [ ] Document versioning
- [ ] Advanced analytics dashboard
- [ ] Docker containerization
- [ ] Kubernetes deployment templates
- [ ] Plugin system for extensibility
- [ ] GraphQL API option

---

**Built with ❤️ by [Shashank Singh](https://github.com/Shashank-Singh90)**

*Making technical documentation accessible and intelligent*
