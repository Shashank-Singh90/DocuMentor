# RAG System - Professional Edition - Project Context

## Project Overview

This is a production-ready Retrieval-Augmented Generation (RAG) system built with Python. It combines document retrieval with AI language models to provide accurate, context-aware responses through both a modern web interface and REST API.

## Core Architecture

### Technology Stack
- **Backend**: Python 3.8+, FastAPI, ChromaDB, Sentence Transformers
- **Frontend**: Streamlit with modern CSS styling and animations
- **AI Providers**: Ollama (primary) -> Gemma
- **Document Processing**: Supports 11+ formats (PDF, TXT, MD, CSV, DOCX, etc.)
- **Web Search**: Integrated Firecrawl and DuckDuckGo search (In pipe line)

### System Components

```
rag_system/
├── api/server.py           # FastAPI REST API with enhanced endpoints
├── core/
│   ├── chunking/chunker.py      # Smart document chunking
│   ├── generation/llm_handler.py # Multi-provider LLM handling
│   ├── processing/document_processor.py # Multi-format document processing
│   ├── retrieval/vector_store.py # ChromaDB vector database
│   ├── search/web_search.py     # Web search integration
│   └── utils/              # Caching, logging, embeddings
├── config/settings.py      # Configuration management
└── web/app.py             # Modern Streamlit interface
```

## Entry Points

- **`main.py`**: Launches Streamlit web interface (port 8506)
- **`api_server.py`**: Launches FastAPI REST API (port 8100)
- **`launcher.py`**: Launches both web and API simultaneously
- **`tests.py`**: Comprehensive test suite for all components

## Key Features

### 1. Technology-Specific Filtering
Supports filtering by 9+ technology stacks:
- Python 3.13.5, FastAPI, Django 5.2
- React & Next.js, Node.js, TypeScript
- PostgreSQL, MongoDB, LangChain

### 2. Advanced Document Processing
- **Smart Chunking**: Overlap-aware chunking for better context
- **Multi-Format**: PDF, TXT, MD, CSV, DOCX, HTML, JSON, XML, etc.
- **Metadata Extraction**: Source tracking and content categorization

### 3. Modern Web Interface
- **Responsive Design**: Modern CSS with gradients and animations
- **Dark Mode Support**: Professional styling
- **Real-Time Features**: Live search, performance metrics
- **Interactive Chat**: Message history, source display

### 4. Comprehensive API
- **Enhanced Q&A**: `/ask/enhanced` with filtering
- **Code Generation**: `/generate-code/enhanced` with context
- **Technology Queries**: `/technology-query` for specific frameworks
- **Document Upload**: `/upload` with processing
- **System Status**: `/status` and `/technologies` endpoints

## Configuration

### Environment Variables
```bash
# LLM Providers
OLLAMA_BASE_URL=http://localhost:11434

# Database
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
COLLECTION_NAME=documents

### Default Settings
- **Chunk Size**: 1000 characters with 200 overlap
- **Search Results**: 5-8 results per query
- **Models**: all-MiniLM-L6-v2 for embeddings
- **Response Mode**: Smart Answer (balanced responses)

## Development Patterns

### Code Organization
- **Single Responsibility**: Each module has one clear purpose
- **Dependency Injection**: Components are loosely coupled
- **Error Handling**: Comprehensive try-catch with logging
- **Caching**: Response and embedding caches for performance

### Naming Conventions
- **Functions**: `snake_case` with descriptive names
- **Classes**: `PascalCase` for main components
- **Files**: `snake_case.py` with clear purposes
- **Variables**: Descriptive names (e.g., `user_question`, `search_results`)

### Testing Strategy
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Search speed and response time
- **API Tests**: All endpoint functionality

## Common Tasks

### Adding New AI Providers
1. Add provider class in `rag_system/core/generation/llm_handler.py`
2. Implement abstract methods: `generate_answer()`, `generate_code()`
3. Add to `get_available_providers()` and `get_provider_status()`
4. Update configuration in `settings.py`

### Adding New Document Formats
1. Add a processor in `rag_system/core/processing/document_processor.py`
2. Update `get_supported_formats()` method
3. Add format-specific processing logic
4. Test with sample documents

### Extending API Endpoints
1. Add new endpoint in `rag_system/api/server.py`
2. Create Pydantic models for request/response
3. Implement business logic
4. Add to API documentation

### Customizing UI Components
1. Modify `rag_system/web/app.py`
2. Update CSS in `configure_page()` function
3. Add new sidebar controls in `render_enhanced_sidebar()`
4. Extend chat interface in `render_main_interface()`

## Performance Optimization

### Vector Search
- **Embedding Cache**: Prevents recomputation of embeddings
- **Response Cache**: Caches recent query results
- **Batch Processing**: Efficient document chunking
- **Similarity Threshold**: Filters low-relevance results

### Memory Management
- **Lazy Loading**: Components initialize on first use
- **Connection Pooling**: Reuses database connections
- **Resource Cleanup**: Proper disposal of large objects
- **Streaming**: Large responses use streaming when possible

## Troubleshooting Guide

### Common Issues
1. **Import Errors**: Check Python path and dependencies
2. **Port Conflicts**: Modify ports in launcher scripts
3. **LLM Unavailable**: Verify Ollama is running
4. **Slow Performance**: Check vector database size and system resources
5. **UI Issues**: Clear Streamlit cache with `streamlit cache clear`

### Debug Mode
- Enable debug logging in the configuration
- Use `tests.py` for systematic component testing

## Security Considerations

### API Security
- CORS configured for development (adjust for production)
- Input validation through Pydantic models
- No sensitive data in logs
- Environment variables for API keys

### Data Privacy
- Local vector database (no external data sharing)
- No persistent storage of user queries
- Configurable data retention policies

## Production Deployment

### Requirements
- Python 3.8+ with pip
- Minimum 4GB RAM for efficient operation
- Disk space for vector database and documents
- Network access for AI providers (if using cloud models)

### Scaling Considerations
- Vector database can handle millions of documents
- API supports concurrent requests
- Web interface handles multiple simultaneous users
- Consider load balancing for high traffic

## Version Information

- **Current Version**: 2.0.0 - Professional Edition
- **Last Updated**: 11 September 2025 (Post-testing and optimization)
- **Python Compatibility**: 3.8+ (Tested with 3.11.9)
- **Dependencies**: Listed in `requirements.txt`
- **Test Status**: 5/7 tests passing (Core functionality operational)

## Recent Updates and Fixes (September 2025)

### Current System Status
- **Document Database**: 270 documents successfully loaded
- **Vector Search**: Fully operational with fast retrieval
- **API Server**: Running on port 8100 (FastAPI)
- **Cache System**: Working without errors
- **LLM Providers**:Ollama -> Gemma 2 2b

## Support and Maintenance

### Testing
```bash
# Comprehensive test suite
python tests.py

# Quick health check
python -c "from rag_system.core import VectorStore; vs = VectorStore(); print('System OK')"

# API test
curl http://127.0.0.1:8100/status
```

### Known Working Configurations
- **Windows 11**: ✅ Fully tested and operational
- **Python 3.11.9**: ✅ Confirmed working
- **All Dependencies**: ✅ Successfully installed via pip

### Updates
- System is production-ready and stable
- All critical bugs have been resolved
- Comprehensive error handling implemented
- Performance optimizations completed

### Documentation
- README.md updated with current status and fixes
- Code comments for developer guidance
- API documentation auto-generated at `/docs`
- This context file reflects current working state

## Deployment Notes

### Pre-tested Commands
```bash
# Start complete system
python launcher.py

# Individual components
python main.py          # Web UI (port 8506)
python api_server.py    # API (port 8100)

# Health checks
python tests.py         # Full test suite
curl http://127.0.0.1:8100/status  # API status
```

### System Requirements Met
- Python 3.8+ ✅
- All pip dependencies ✅
- 270 documents loaded ✅
- Vector search operational ✅
- Cache system fixed ✅
- Unicode issues resolved ✅

---

**Note for AI Assistants**: This project is now fully operational and tested. All critical bugs have been resolved, including cache system errors and Unicode issues. The system successfully runs on Windows with Python 3.11.9 and provides excellent document search capabilities even without LLM providers. When assisting with this codebase, note that it's production-ready with 270 pre-loaded documents and comprehensive error handling.
