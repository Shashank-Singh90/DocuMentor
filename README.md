# DocuMentor

An AI-powered documentation assistant and Retrieval-Augmented Generation (RAG) system that provides intelligent search, question-answering, and code generation capabilities across multiple programming frameworks and technologies.

## Overview

DocuMentor solves a common developer problem: finding accurate, context-aware answers from documentation without manual searching. It combines semantic search with AI-powered generation to deliver intelligent responses, working code implementations, and comprehensive documentation references.

### Key Capabilities

- **Smart Documentation Search**: Semantic search using vector embeddings with technology-specific filtering
- **AI-Powered Q&A**: Multi-provider LLM support (Ollama, OpenAI, Gemini) for intelligent responses
- **Advanced Code Generation**: Context-aware code generation with best practices and error handling
- **Real-Time Web Search**: Integrated Firecrawl and DuckDuckGo for comprehensive information retrieval
- **Multi-Format Document Processing**: Support for PDFs, Word docs, presentations, spreadsheets, and more

## Technology Stack

### Core Technologies

- **Backend**: FastAPI (REST API with OpenAPI), Python 3.x
- **Frontend**: Streamlit (interactive web UI with dark/light mode)
- **Vector Database**: ChromaDB with persistent storage
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2)
- **Document Processing**: LangChain, pypdf, python-docx, python-pptx, openpyxl, pandas

### AI/ML Integration

- **Ollama**: Local LLM support (default: gemma2:2b)
- **OpenAI**: GPT-3.5-turbo integration
- **Google Gemini**: gemini-pro support
- **Automatic Fallback**: Switches between providers seamlessly

### Infrastructure

- **Security**: API key authentication, rate limiting (SlowAPI)
- **Monitoring**: Prometheus metrics, structured logging
- **Caching**: Response cache, embedding cache for performance
- **Web Search**: Firecrawl (local/API), DuckDuckGo fallback

## Supported Technologies

DocuMentor comes pre-embedded with comprehensive documentation for:

- Python 3.13.5
- FastAPI
- Django 5.2
- React & Next.js
- Node.js
- TypeScript
- PostgreSQL
- MongoDB
- LangChain

## Quick Start

### Prerequisites

- Python 3.8+
- Ollama (for local LLM) or API keys for OpenAI/Gemini
- 2GB+ RAM recommended

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/DocuMentor.git
   cd DocuMentor
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Start the system**

   **Option 1: Complete system (API + UI)**
   ```bash
   python launcher.py
   ```

   **Option 2: Individual components**
   ```bash
   # Streamlit UI only (port 8506)
   python main.py --port 8506

   # FastAPI server only (port 8100)
   python api_server.py --port 8100
   ```

5. **Access the application**
   - Web UI: http://localhost:8506
   - API Docs: http://localhost:8100/docs
   - Metrics: http://localhost:8100/metrics

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```bash
# Application
APP_NAME="DocuMentor"
DEBUG=false

# Server
HOST=127.0.0.1
PORT=8501

# Security (optional)
API_KEY=your-secure-api-key-min-16-chars

# Rate Limiting (requests per minute)
RATE_LIMIT_SEARCH=60
RATE_LIMIT_UPLOAD=10
RATE_LIMIT_QUERY=30
RATE_LIMIT_GENERATION=20

# LLM Configuration
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_HOST=localhost:11434
OLLAMA_MODEL=gemma2:2b
OLLAMA_TIMEOUT=120

# Optional: OpenAI
OPENAI_API_KEY=sk-your-openai-key

# Optional: Gemini
GEMINI_API_KEY=your-gemini-key

# Vector Database
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
COLLECTION_NAME=documents
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Chunking
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Caching
CACHE_DIR=./data/cache
CACHE_TTL=3600

# File Upload
MAX_FILE_SIZE=52428800  # 50MB

# Web Search (optional)
FIRECRAWL_API_KEY=your-firecrawl-key
ENABLE_WEB_SEARCH=true
ENABLE_CODE_GENERATION=true
```

## Features

### 1. Intelligent Search

- **Semantic Search**: Vector-based similarity search using ChromaDB
- **Technology Filtering**: Filter by specific frameworks/languages
- **Context-Aware Retrieval**: Smart chunking preserves code blocks and structure
- **Hybrid Search**: Combines local documentation with web search

### 2. AI-Powered Q&A

Three response modes:

- **Smart Answer**: Balanced, comprehensive responses
- **Code Generation**: Working code implementations with best practices
- **Detailed Sources**: Extensive documentation references with metadata

### 3. Code Generation

- Language-specific code generation
- Technology-aware context retrieval
- Multiple styles: complete implementations, snippets, explanations
- Error handling and best practices included

### 4. Document Management

**Supported Formats**:
- Text: .txt, .md
- Documents: .pdf, .docx, .rtf, .odt
- Data: .csv, .xlsx, .xls
- Presentations: .pptx

**Processing Features**:
- Smart content extraction with metadata
- Table and structured content preservation
- Automatic chunking and embedding
- Technology tag assignment

### 5. Web Search Integration

- **Firecrawl**: Primary search with content crawling
- **DuckDuckGo**: Free fallback (no API key required)
- **Content Extraction**: Markdown/HTML parsing
- **Context Integration**: Seamlessly combines with local docs

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│  ┌─────────────────┐              ┌─────────────────┐       │
│  │  Streamlit UI   │              │   FastAPI REST  │       │
│  │  (Port 8506)    │              │   (Port 8100)   │       │
│  └────────┬────────┘              └────────┬────────┘       │
└───────────┼─────────────────────────────────┼───────────────┘
            │                                 │
            └────────────────┬────────────────┘
                             ▼
            ┌────────────────────────────────┐
            │    RAG System Core Layer       │
            │  • SmartChunker                │
            │  • VectorStore (ChromaDB)      │
            │  • LLM Handler (Multi-provider)│
            │  • Document Processor          │
            │  • Web Search Provider         │
            └────────────────┬───────────────┘
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
    ┌──────────────┐              ┌──────────────────┐
    │  ChromaDB    │              │  External APIs   │
    │  Persistent  │              │  • Ollama        │
    │  Vector DB   │              │  • OpenAI        │
    └──────────────┘              │  • Gemini        │
                                  │  • Firecrawl     │
                                  └──────────────────┘
```

## API Reference

### General Endpoints

- `GET /` - API information
- `GET /status` - System status and capabilities
- `GET /metrics` - Prometheus metrics

### Technology Endpoints

- `GET /technologies` - List all available technologies
- `GET /technologies/{technology}/stats` - Technology-specific statistics
- `POST /technology-query` - Technology-filtered queries

### Q&A Endpoints

- `POST /ask` - Legacy Q&A endpoint
- `POST /ask/enhanced` - Enhanced Q&A with filtering

### Code Generation

- `POST /generate-code/enhanced` - Enhanced code generation

### Document Management

- `POST /upload` - Upload and process documents (multipart/form-data)

### Example Request

```bash
curl -X POST "http://localhost:8100/ask/enhanced" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I create a FastAPI endpoint with authentication?",
    "technology": "fastapi",
    "response_mode": "code_generation"
  }'
```

## Project Structure

```
DocuMentor/
├── rag_system/                    # Core RAG system package
│   ├── core/                      # Core functionality
│   │   ├── chunking/             # Smart document chunking
│   │   ├── retrieval/            # Vector search (ChromaDB)
│   │   ├── generation/           # Multi-provider LLM
│   │   ├── processing/           # Document processing
│   │   ├── search/               # Web search integration
│   │   └── utils/                # Utilities & caching
│   ├── api/                       # FastAPI REST API
│   │   ├── server.py             # Main API application
│   │   └── middleware/           # Auth & validation
│   ├── web/                       # Streamlit web interface
│   │   └── app.py                # UI application
│   └── config/                    # Configuration management
│       └── settings.py           # Pydantic settings
├── data/                          # Data storage
│   ├── preembedded/              # Pre-embedded documentation
│   ├── scraped/                  # Scraped documentation
│   ├── chroma_db/                # Vector database (gitignored)
│   ├── cache/                    # System cache (gitignored)
│   └── uploads/                  # User uploads (gitignored)
├── launcher.py                    # System launcher
├── main.py                        # Streamlit entry point
├── api_server.py                  # FastAPI entry point
├── tests.py                       # Comprehensive test suite
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment template
└── LICENSE                        # MIT License
```

## Performance Features

### Smart Caching

- **Embedding Cache**: Persistent disk-based cache for embeddings (~90% faster for repeated texts)
- **Response Cache**: In-memory cache with TTL and LRU eviction
- **Model-Specific Caching**: Separate caches for different embedding models

### Optimization

- **Dynamic Batch Processing**: Automatic batch size calculation based on content length
- **Parallel Processing**: ThreadPoolExecutor for concurrent operations
- **Content Truncation**: Smart context limits prevent LLM confusion
- **File Locking**: Prevents ChromaDB corruption in concurrent environments

### Monitoring

- **Prometheus Metrics**: Request duration, LLM usage, cache performance
- **Structured Logging**: Rich console output with log levels
- **Performance Benchmarks**: Built-in test suite with timing metrics

## Security

### Authentication

- Optional API key authentication (configurable via environment)
- Minimum 16-character key requirement
- Applied to all endpoints when enabled

### Rate Limiting

- IP-based rate limiting using SlowAPI
- Configurable per-endpoint limits:
  - Search: 60 requests/minute
  - Upload: 10 requests/minute
  - Query: 30 requests/minute
  - Code Generation: 20 requests/minute

### Input Validation

- File type validation using python-magic
- File size limits (default: 50MB)
- Request payload validation with Pydantic
- Sanitized file uploads

## Testing

Run the comprehensive test suite:

```bash
python tests.py
```

**Test Coverage**:
- System imports and configuration
- Vector store functionality
- Document processing (all formats)
- LLM provider connectivity
- API server endpoints
- Performance benchmarks

## Troubleshooting

### Common Issues

**ChromaDB Lock Errors**
```bash
# Remove lock file
rm data/chroma_db/*.lock
```

**Ollama Connection Failed**
```bash
# Ensure Ollama is running
ollama serve
# Test connection
curl http://localhost:11434/api/tags
```

**Import Errors**
```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

**Port Already in Use**
```bash
# Kill process on port
lsof -ti:8506 | xargs kill -9
```

### Performance Tuning

- Increase `MAX_WORKERS` for faster parallel processing
- Adjust `CHUNK_SIZE` and `CHUNK_OVERLAP` for better context
- Enable embedding cache for faster repeated queries
- Use Ollama for free, private LLM inference

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **ChromaDB**: Vector database for semantic search
- **LangChain**: Document processing framework
- **Sentence Transformers**: Embedding models
- **FastAPI**: Modern API framework
- **Streamlit**: Interactive web UI framework
- **Ollama**: Local LLM infrastructure

## Support

For issues, questions, or contributions:

- Open an issue on GitHub
- Check the API documentation at `/docs`
- Review the test suite for usage examples

---

**Built with ❤️ for developers who love documentation**
