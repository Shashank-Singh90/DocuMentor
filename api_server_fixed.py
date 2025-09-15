#!/usr/bin/env python3
"""
DocuMentor API Server - Fixed Version
Fixed issues:
1. Updated to modern FastAPI lifespan events
2. Proper upload endpoint handling
3. Better error handling
"""
import time
import uvicorn
from contextlib import asynccontextmanager
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import our components
try:
    from src.retrieval.vector_store import ChromaVectorStore
    from src.generation.ollama_handler import OllamaLLMHandler
    from src.ingestion.document_processor import DocumentProcessor  # Fixed import
    from src.utils.logger import get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    raise

logger = get_logger(__name__)

# Global variables for components
vector_store = None
llm_handler = None
document_processor = None
start_time = time.time()

# Response Models
class SearchQuery(BaseModel):
    query: str
    k: int = 5

class QuestionQuery(BaseModel):
    question: str
    k: int = 5
    temperature: float = 0.1
    max_tokens: Optional[int] = None

class SearchResult(BaseModel):
    content: str
    metadata: Dict[str, Any]
    score: float

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total_found: int
    query: str
    search_time: float

class QuestionResponse(BaseModel):
    answer: str
    sources: List[SearchResult]
    question: str
    response_time: float
    confidence: float
    search_results_count: int

class StatsResponse(BaseModel):
    total_chunks: int
    sources: Dict[str, int]
    total_sources: int
    api_version: str
    status: str

class HealthResponse(BaseModel):
    status: str
    version: str
    components: Dict[str, str]
    uptime: float

class UploadResponse(BaseModel):
    success: bool
    message: str
    chunks_added: int
    chunks_failed: int
    total_chunks_in_file: int
    file_type: str
    filename: str
    total_chunks_in_db: int

# Modern FastAPI lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Modern FastAPI lifespan event handler"""
    # Startup
    logger.info("🚀 Starting DocuMentor API server...")
    
    global vector_store, llm_handler, document_processor
    
    try:
        # Initialize vector store
        logger.info("📚 Initializing vector store...")
        vector_store = ChromaVectorStore()
        
        # Initialize LLM handler
        logger.info("🤖 Initializing LLM handler...")
        llm_handler = OllamaLLMHandler()
        
        # Initialize document processor
        logger.info("📄 Initializing document processor...")
        document_processor = DocumentProcessor()
        
        # Get initial stats
        stats = vector_store.get_collection_stats()
        total_chunks = stats.get('total_chunks', 0)
        total_sources = len(stats.get('sources', {}))
        
        logger.info(f"✅ DocuMentor API ready with {total_chunks} chunks across {total_sources} sources")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        raise
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("🛑 Shutting down DocuMentor API server...")

# Create FastAPI app with modern lifespan
app = FastAPI(
    title="DocuMentor API",
    description="AI-powered documentation assistant",
    version="1.0.0",
    lifespan=lifespan  # Modern lifespan instead of on_event
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to DocuMentor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "stats": "/stats",
        "upload": "/upload-document",
        "features": "Search, Ask Questions, Upload Documents"
    }

# Health check endpoint
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test vector store
        if vector_store:
            vector_status = "healthy"
            try:
                vector_store.get_collection_stats()
            except Exception:
                vector_status = "error"
        else:
            vector_status = "not_initialized"
        
        # Test LLM handler
        if llm_handler and hasattr(llm_handler, 'ollama_available'):
            llm_status = "healthy" if llm_handler.ollama_available else "offline"
        else:
            llm_status = "not_initialized"
        
        uptime = time.time() - start_time
        
        return HealthResponse(
            status="healthy" if vector_status == "healthy" and llm_status == "healthy" else "degraded",
            version="1.0.0",
            components={
                "vector_store": vector_status,
                "llm_handler": llm_status,
                "document_processor": "healthy" if document_processor else "not_initialized"
            },
            uptime=uptime
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Stats endpoint
@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get system statistics"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        stats = vector_store.get_collection_stats()
        
        return StatsResponse(
            total_chunks=stats.get('total_chunks', 0),
            sources=stats.get('sources', {}),
            total_sources=len(stats.get('sources', {})),
            api_version="1.0.0",
            status="active"
        )
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")

# Sources endpoint
@app.get("/sources")
async def get_sources():
    """Get list of available documentation sources"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        stats = vector_store.get_collection_stats()
        sources = stats.get('sources', {})
        
        return list(sources.keys())
        
    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get sources: {str(e)}")

# Search endpoint
@app.post("/search", response_model=SearchResponse)
async def search_documents(query: SearchQuery):
    """Search through documentation"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        start_time_search = time.time()
        
        # Perform search
        results = vector_store.search(query.query, k=query.k)
        
        search_time = time.time() - start_time_search
        
        # Format results
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                content=result.get('content', ''),
                metadata=result.get('metadata', {}),
                score=result.get('score', 0.0)
            ))
        
        return SearchResponse(
            results=search_results,
            total_found=len(search_results),
            query=query.query,
            search_time=search_time
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Question answering endpoint
@app.post("/ask", response_model=QuestionResponse)
async def ask_question(question: QuestionQuery):
    """Ask a question and get AI-powered answer"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        if not llm_handler:
            raise HTTPException(status_code=503, detail="LLM handler not initialized")
        
        start_time_question = time.time()
        
        # Search for relevant documents
        search_results = vector_store.search(question.question, k=question.k)
        
        # Generate answer using LLM
        answer = llm_handler.generate_answer(
            question=question.question,
            search_results=search_results,
            max_tokens=question.max_tokens,
            temperature=question.temperature
        )
        
        response_time = time.time() - start_time_question
        
        # Format search results
        formatted_results = []
        for result in search_results:
            formatted_results.append(SearchResult(
                content=result.get('content', ''),
                metadata=result.get('metadata', {}),
                score=result.get('score', 0.0)
            ))
        
        # Calculate confidence based on search results quality
        confidence = min(len(search_results) / question.k, 1.0) if search_results else 0.0
        
        return QuestionResponse(
            answer=answer,
            sources=formatted_results,
            question=question.question,
            response_time=response_time,
            confidence=confidence,
            search_results_count=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")

# Fixed upload endpoint
@app.post("/upload-document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document (Markdown, CSV, or Text)"""
    try:
        if not vector_store:
            raise HTTPException(status_code=503, detail="Vector store not initialized")
        
        if not document_processor:
            raise HTTPException(status_code=503, detail="Document processor not initialized")
        
        # Check file type
        allowed_extensions = ['md', 'markdown', 'csv', 'txt', 'text']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type '{file_extension}'. Allowed: {allowed_extensions}"
            )
        
        logger.info(f"📤 Processing uploaded file: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Process document into chunks
        chunks = document_processor.process_uploaded_file(file_content, file.filename, file_extension)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not process the file - no content extracted")
        
        # Add chunks to vector store
        added_count = 0
        failed_count = 0
        
        for i, chunk in enumerate(chunks):
            try:
                doc_id = f"upload_{file.filename}_{i}_{hash(chunk['content']) % 10000}"
                
                # Use collection directly (most reliable method)
                vector_store.collection.add(
                    documents=[chunk['content']],
                    metadatas=[chunk['metadata']],
                    ids=[doc_id]
                )
                
                added_count += 1
                
            except Exception as e:
                logger.warning(f"Error adding chunk {i}: {e}")
                failed_count += 1
                continue
        
        if added_count == 0:
            raise HTTPException(status_code=500, detail="Failed to add any chunks to the knowledge base")
        
        # Get updated stats
        try:
            updated_stats = vector_store.get_collection_stats()
            total_chunks_now = updated_stats.get('total_chunks', 0)
        except:
            total_chunks_now = 0
        
        logger.info(f"✅ Successfully added {added_count} chunks from {file.filename}")
        
        return UploadResponse(
            success=True,
            message=f"Successfully processed {file.filename}",
            chunks_added=added_count,
            chunks_failed=failed_count,
            total_chunks_in_file=len(chunks),
            file_type=file_extension,
            filename=file.filename,
            total_chunks_in_db=total_chunks_now
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

# Upload info endpoint
@app.get("/upload-info")
async def get_upload_info():
    """Get information about file upload capabilities"""
    current_stats = {"total_chunks": 0, "sources": 0}
    
    if vector_store:
        try:
            stats = vector_store.get_collection_stats()
            current_stats = {
                "total_chunks": stats.get('total_chunks', 0),
                "sources": len(stats.get('sources', {}))
            }
        except:
            pass
    
    return {
        "supported_formats": [
            {
                "extension": "md",
                "description": "Markdown files - parsed by sections and headers",
                "max_size": "10MB recommended"
            },
            {
                "extension": "csv", 
                "description": "CSV data files - creates overview and column analysis",
                "max_size": "5MB recommended"
            },
            {
                "extension": "txt",
                "description": "Plain text files - chunked intelligently",
                "max_size": "10MB recommended"
            }
        ],
        "processing_info": {
            "markdown": "Parses headers to create logical sections",
            "csv": "Creates data overview, column analysis, and row samples", 
            "text": "Smart chunking with sentence boundaries"
        },
        "usage": {
            "endpoint": "/upload-document",
            "method": "POST",
            "content_type": "multipart/form-data",
            "parameter": "file"
        },
        "current_stats": current_stats
    }

# Development server runner
def run_server():
    """Run the development server"""
    logger.info("🚀 Starting DocuMentor API development server...")
    uvicorn.run(
        "api_server_fixed:app",  # Updated module name
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()





