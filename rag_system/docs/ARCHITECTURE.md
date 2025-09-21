# RAG System Architecture

## Overview

The RAG System is built with a modular, scalable architecture designed for production use. It follows clean architecture principles with clear separation of concerns.

## Core Components

### 1. Core Layer (`rag_system/core/`)

#### Chunking Module (`chunking/`)
- **Purpose**: Intelligent document processing and chunking
- **Key Features**:
  - Async parallel processing with ThreadPoolExecutor
  - Content-aware chunking (preserves code blocks, markdown structure)
  - Dynamic batch sizing based on content complexity
  - Support for multiple document formats

#### Generation Module (`generation/`)
- **Purpose**: LLM integration and response generation
- **Key Features**:
  - Streaming response generation
  - Multiple response formats (definition, tutorial, examples)
  - Template-based fallback responses
  - Response caching integration

#### Retrieval Module (`retrieval/`)
- **Purpose**: Vector database operations and semantic search
- **Key Features**:
  - Optimized ChromaDB configuration
  - Embedding caching for performance
  - Dynamic batch size calculation
  - Advanced error handling and retry logic

#### Utils Module (`utils/`)
- **Purpose**: Shared utilities and caching systems
- **Components**:
  - **Logger**: Centralized logging with configurable levels
  - **Response Cache**: LLM response caching with smart key generation
  - **Embedding Cache**: Text embedding caching with persistence

### 2. Configuration Layer (`config/`)
- **Purpose**: Centralized configuration management
- **Features**:
  - Pydantic-based settings with validation
  - Environment variable support
  - Automatic directory creation
  - Type safety and documentation

### 3. Web Layer (`web/`)
- **Purpose**: Streamlit-based user interface
- **Features**:
  - Professional UI with custom styling
  - Real-time streaming responses
  - Document upload and processing
  - Performance metrics display
  - Responsive design

## Data Flow

```
User Input → Web Interface → Core Processing → Vector Search → LLM Generation → Response
     ↓              ↓              ↓              ↓              ↓              ↓
Document Upload → Chunking → Embedding → Storage → Retrieval → Context → Answer
```

### Detailed Flow

1. **Document Processing**:
   - User uploads document via web interface
   - Document is processed by `SmartChunker`
   - Content is split into semantically meaningful chunks
   - Chunks are embedded using sentence transformers
   - Embeddings are stored in ChromaDB with metadata

2. **Query Processing**:
   - User submits question via web interface
   - System checks response cache for existing answer
   - If not cached, performs vector similarity search
   - Retrieves top-k relevant document chunks
   - Generates response using LLM with retrieved context
   - Caches response for future use

## Performance Optimizations

### Caching Strategy

1. **Response Cache**:
   - Caches complete LLM responses
   - Key generated from query + context hash
   - LRU eviction with configurable size limits
   - Persistent storage for cross-session caching

2. **Embedding Cache**:
   - Caches text embeddings to avoid recomputation
   - Batch operations for efficiency
   - Size-based eviction strategy
   - Memory-mapped storage for large caches

### Parallel Processing

1. **Document Chunking**:
   - ThreadPoolExecutor with 4 workers
   - Batch processing with timeout handling
   - Error isolation (failed docs don't block others)

2. **Vector Operations**:
   - Dynamic batch sizing based on content length
   - Optimized ChromaDB settings for performance
   - Bulk upsert operations

## Scalability Considerations

### Horizontal Scaling
- Stateless design enables multiple instance deployment
- Shared vector database for consistency
- Cache synchronization strategies

### Vertical Scaling
- Configurable worker thread counts
- Memory usage optimization
- Batch size tuning based on system resources

## Security

### Data Protection
- Local processing (no data leaves system)
- Configurable API authentication
- Input validation and sanitization

### Error Handling
- Comprehensive exception handling
- Graceful degradation
- Detailed logging for debugging

## Monitoring & Observability

### Metrics Collection
- Response times
- Cache hit rates
- Memory usage
- Error rates
- Document processing statistics

### Logging
- Structured logging with configurable levels
- Request/response tracing
- Performance monitoring
- Error tracking

## Configuration Management

### Settings Hierarchy
1. Environment variables (highest priority)
2. `.env` file
3. Default values (lowest priority)

### Key Configuration Areas
- Model settings (Ollama configuration)
- Performance tuning (batch sizes, workers)
- Caching parameters
- Security settings
- Storage locations

## Deployment

### Local Development
```bash
python main.py --mode web --debug
```

### Production
```bash
python main.py --mode web --host 0.0.0.0 --port 8501
```

### Container Deployment
- Dockerfile for containerization
- Docker Compose for multi-service setup
- Environment-based configuration

## Future Enhancements

### Planned Features
- REST API layer
- CLI interface
- Advanced retrieval strategies (hybrid search)
- Multi-user support
- Real-time collaboration

### Performance Improvements
- GPU acceleration for embeddings
- Distributed vector storage
- Advanced caching strategies
- Load balancing

## Dependencies

### Core Dependencies
- **ChromaDB**: Vector database and similarity search
- **Sentence Transformers**: Text embeddings
- **Streamlit**: Web interface framework
- **Pydantic**: Configuration and validation
- **LangChain**: LLM integration framework

### Optional Dependencies
- **Ollama**: Local LLM runtime
- **FastAPI**: Future REST API
- **Redis**: Distributed caching (future)

## Best Practices

### Code Organization
- Clean architecture with dependency inversion
- Single responsibility principle
- Type hints and documentation
- Comprehensive error handling

### Performance
- Async/await for I/O operations
- Caching at multiple levels
- Resource cleanup and management
- Memory usage optimization

### Maintainability
- Modular design with clear interfaces
- Configuration-driven behavior
- Comprehensive logging
- Unit and integration tests