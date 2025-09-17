# Create api_server_production.py
@"
#!/usr/bin/env python3
"""
DocuMentor API Server - Production Version
Python 3.11 Compatible Professional Implementation
"""
import asyncio
import time
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exception_handlers import http_exception_handler
from pydantic import BaseModel, Field
from loguru import logger
import uvicorn

# Import our components
from src.config.settings import settings, create_directories
from src.retrieval.vector_store import ChromaVectorStore
from src.generation.ollama_handler import OllamaLLMHandler
from src.ingestion.document_processor import DocumentProcessor

# Global components
vector_store: Optional[ChromaVectorStore] = None
llm_handler: Optional[OllamaLLMHandler] = None
document_processor: Optional[DocumentProcessor] = None
start_time = time.time()

# Configure logging
logger.add(
    settings.log_file,
    rotation="10 MB",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}"
)

# Request Models
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000, description="Question to ask")
    k: int = Field(5, ge=1, le=20, description="Number of results to retrieve")
    temperature: float = Field(0.1, ge=0.0, le=2.0, description="Generation temperature")
    max_tokens: Optional[int] = Field(None, ge=1, le=4096, description="Maximum tokens to generate")

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Search query")
    k: int = Field(5, ge=1, le=20, description="Number of results to return")

# Response Models
class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, str]
    uptime_seconds: float
    timestamp: str

class QuestionResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    question: str
    response_time_seconds: float
    confidence_score: Optional[float] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    query: str
    search_time_seconds: float

class StatsResponse(BaseModel):
    total_chunks: int
    sources: Dict[str, Any]
    total_sources: int
    uptime_seconds: float
    api_version: str

# Lifespan management
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    # Startup
    logger.info("Starting DocuMentor API server...")
    
    global vector_store, llm_handler, document_processor
    
    try:
        # Create required directories
        create_directories(settings)
        logger.info("Required directories created")
        
        # Initialize components
        logger.info("Initializing vector store...")
        vector_store = ChromaVectorStore()
        
        logger.info("Initializing LLM handler...")
        llm_handler = OllamaLLMHandler()
        
        logger.info("Initializing document processor...")
        document_processor = DocumentProcessor()
        
        # Verify components
        await verify_components()
        
        logger.info("DocuMentor API ready for requests")
        
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Shutting down DocuMentor API server...")

async def verify_components():
    """Verify all components are working"""
    checks = []
    
    # Check vector store
    try:
        stats = vector_store.get_collection_stats()
        total_chunks = stats.get("total_chunks", 0)
        checks.append(f"Vector store: {total_chunks} chunks")
        logger.info(f"Vector store initialized with {total_chunks} chunks")
    except Exception as e:
        logger.warning(f"Vector store check failed: {e}")
        checks.append("Vector store: warning")
    
    # Check LLM
    try:
        # Quick test with minimal tokens
        test_response = llm_handler.generate("Test", max_tokens=5)
        checks.append(f"LLM: Response length {len(test_response)} chars")
        logger.info("LLM handler verification successful")
    except Exception as e:
        logger.warning(f"LLM check failed: {e}")
        checks.append("LLM: warning")
    
    logger.info("Component verification complete: " + ", ".join(checks))

# Create FastAPI app
app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure properly for production
)

# Exception handlers
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request, exc):
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return await http_exception_handler(request, exc)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )

# Dependency injection
async def get_vector_store() -> ChromaVectorStore:
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not available")
    return vector_store

async def get_llm_handler() -> OllamaLLMHandler:
    if not llm_handler:
        raise HTTPException(status_code=503, detail="LLM handler not available")
    return llm_handler

# API Endpoints
@app.get("/", response_model=Dict[str, Any])
async def root():
    """API root endpoint with server information"""
    return {
        "message": "Welcome to DocuMentor API",
        "version": settings.api_version,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "ask": "/ask",
            "search": "/search",
            "upload": "/upload",
            "stats": "/stats"
        },
        "python_version": "3.11",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check"""
    components = {
        "vector_store": "ok" if vector_store else "unavailable",
        "llm_handler": "ok" if llm_handler else "unavailable",
        "document_processor": "ok" if document_processor else "unavailable"
    }
    
    overall_status = "healthy" if all(v == "ok" for v in components.values()) else "degraded"
    
    return HealthResponse(
        status=overall_status,
        version=settings.api_version,
        components=components,
        uptime_seconds=time.time() - start_time,
        timestamp=datetime.utcnow().isoformat()
    )

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(
    request: QuestionRequest,
    vs: ChromaVectorStore = Depends(get_vector_store),
    llm: OllamaLLMHandler = Depends(get_llm_handler)
):
    """Ask a question and get an AI-powered answer"""
    start_time_req = time.time()
    
    try:
        logger.info(f"Processing question: {request.question[:100]}...")
        
        # Search for relevant context
        search_results = vs.search(request.question, k=request.k)
        
        if not search_results:
            logger.info("No search results found, using direct generation")
            response = llm.generate(
                f"Question: {request.question}\nAnswer:",
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            sources = []
        else:
            logger.info(f"Found {len(search_results)} search results")
            # Generate with context
            context = "\n---\n".join([r["content"] for r in search_results])
            prompt = f"Context:\n{context}\n\nQuestion: {request.question}\nAnswer:"
            
            response = llm.generate(
                prompt,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            sources = search_results[:3]  # Return top 3 sources
        
        response_time = time.time() - start_time_req
        logger.info(f"Question processed successfully in {response_time:.2f} seconds")
        
        return QuestionResponse(
            answer=response,
            sources=sources,
            question=request.question,
            response_time_seconds=response_time
        )
        
    except Exception as e:
        logger.error(f"Error in ask_question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to process question: {str(e)}")

@app.post("/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    vs: ChromaVectorStore = Depends(get_vector_store)
):
    """Search through the document collection"""
    start_time_req = time.time()
    
    try:
        logger.info(f"Searching for: {request.query}")
        results = vs.search(request.query, k=request.k)
        
        search_time = time.time() - start_time_req
        logger.info(f"Search completed in {search_time:.2f} seconds, found {len(results)} results")
        
        return SearchResponse(
            results=results,
            total_found=len(results),
            query=request.query,
            search_time_seconds=search_time
        )
        
    except Exception as e:
        logger.error(f"Error in search_documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/stats", response_model=StatsResponse)
async def get_stats(vs: ChromaVectorStore = Depends(get_vector_store)):
    """Get system statistics"""
    try:
        stats = vs.get_collection_stats()
        return StatsResponse(
            total_chunks=stats.get("total_chunks", 0),
            sources=stats.get("sources", {}),
            total_sources=len(stats.get("sources", {})),
            uptime_seconds=time.time() - start_time,
            api_version=settings.api_version
        )
    except Exception as e:
        logger.error(f"Error getting stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

def run_server():
    """Run the production server"""
    logger.info(f"Starting server on {settings.host}:{settings.port}")
    uvicorn.run(
        "api_server_production:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
        access_log=True
    )

if __name__ == "__main__":
    run_server()
"@ | Out-File -FilePath "api_server_production.py" -Encoding utf8
