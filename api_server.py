import sys
import os
sys.path.insert(0, os.getcwd())

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import time
import uvicorn
import pandas as pd
import io

# Import our DocuMentor components
from src.retrieval.vector_store import ChromaVectorStore
from src.utils.logger import get_logger

# Try to import Ollama handler, fallback to simple
try:
    from src.generation.ollama_handler import OllamaLLMHandler
    LLM_HANDLER_CLASS = OllamaLLMHandler
except ImportError:
    from src.generation.llm_handler import SimpleLLMHandler
    LLM_HANDLER_CLASS = SimpleLLMHandler

logger = get_logger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="DocuMentor API",
    description="AI-powered documentation assistant API with 9+ technology sources and document upload",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware for web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components globally
vector_store = None
llm_handler = None

# Pydantic models for API
class SearchRequest(BaseModel):
    query: str
    k: int = 5
    source_filter: Optional[str] = None
    doc_type_filter: Optional[str] = None

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_found: int
    response_time: float

class QuestionRequest(BaseModel):
    question: str
    k: int = 5
    source_filter: Optional[str] = None
    doc_type_filter: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.1

class QuestionResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float
    response_time: float
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
    total_chunks_in_db: Any

# Global variables for tracking
start_time = time.time()

@app.on_event("startup")
async def startup_event():
    """Initialize components on startup"""
    global vector_store, llm_handler
    
    logger.info("🚀 Starting DocuMentor API server...")
    
    try:
        # Initialize vector store
        logger.info("📚 Initializing vector store...")
        vector_store = ChromaVectorStore()
        
        # Initialize LLM handler
        logger.info("🤖 Initializing LLM handler...")
        llm_handler = LLM_HANDLER_CLASS()
        
        # Get initial stats
        stats = vector_store.get_collection_stats()
        logger.info(f"✅ DocuMentor API ready with {stats.get('total_chunks', 0)} chunks across {len(stats.get('sources', {}))} sources")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize components: {e}")
        raise

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

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        # Test vector store
        vector_status = "healthy" if vector_store else "unhealthy"
        
        # Test LLM handler
        llm_status = "healthy" if llm_handler else "unhealthy"
        
        return HealthResponse(
            status="healthy" if vector_status == "healthy" and llm_status == "healthy" else "unhealthy",
            version="1.0.0",
            components={
                "vector_store": vector_status,
                "llm_handler": llm_status,
                "database": "connected",
                "upload_processor": "available"
            },
            uptime=time.time() - start_time
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get knowledge base statistics"""
    try:
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
        raise HTTPException(status_code=500, detail="Failed to retrieve statistics")

@app.post("/search", response_model=SearchResponse)
async def search_documents(request: SearchRequest):
    """Search for relevant documents"""
    start_time_req = time.time()
    
    try:
        # Prepare filters
        filters = {}
        if request.source_filter:
            filters['source'] = request.source_filter.lower()
        if request.doc_type_filter:
            filters['doc_type'] = request.doc_type_filter.lower()
        
        # Perform search
        results = vector_store.search(
            query=request.query,
            k=request.k,
            filter_dict=filters if filters else None
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'content': result.get('content', ''),
                'metadata': result.get('metadata', {}),
                'score': result.get('score', 0.0)
            })
        
        return SearchResponse(
            results=formatted_results,
            total_found=len(results),
            response_time=time.time() - start_time_req
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question and get an AI-generated answer"""
    start_time_req = time.time()
    
    try:
        # Prepare filters
        filters = {}
        if request.source_filter:
            filters['source'] = request.source_filter.lower()
        if request.doc_type_filter:
            filters['doc_type'] = request.doc_type_filter.lower()
        
        # Search for relevant documents
        search_results = vector_store.search(
            query=request.question,
            k=request.k,
            filter_dict=filters if filters else None
        )
        
        # Always call Gemma 3, even with no search results
        if hasattr(llm_handler, 'generate_answer'):
            answer = llm_handler.generate_answer(
                question=request.question,
                search_results=search_results if search_results else [],
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
        else:
            answer = f"I couldn't find specific information about '{request.question}' in the available documentation. Try rephrasing your question or check if it's related to our supported technologies: LangChain, FastAPI, Django, React, Python, Docker, PostgreSQL, MongoDB, TypeScript, or your uploaded documents."

        if not search_results:
            return QuestionResponse(
                answer=answer,
                sources=[],
                confidence=0.0,
                response_time=time.time() - start_time_req,
                search_results_count=0
            )
        
        # Generate answer using LLM
        if hasattr(llm_handler, 'generate_answer'):
            answer = llm_handler.generate_answer(
                question=request.question, 
                search_results=search_results,
                max_tokens=request.max_tokens,
                temperature=request.temperature
            )
        else:
            # Fallback simple answer
            top_result = search_results[0]
            content = top_result.get('content', '')[:500]
            answer = f"Based on the documentation: {content}..."
        
        # Calculate confidence (average of top 3 scores)
        top_scores = [r.get('score', 0) for r in search_results[:3]]
        confidence = sum(top_scores) / len(top_scores) if top_scores else 0.0
        
        # Format sources
        sources = []
        for result in search_results[:5]:  # Return top 5 sources
            metadata = result.get('metadata', {})
            sources.append({
                'title': metadata.get('title', 'Unknown'),
                'source': metadata.get('source', 'unknown'),
                'url': metadata.get('url', '#'),
                'doc_type': metadata.get('doc_type', 'general'),
                'score': result.get('score', 0),
                'content_preview': result.get('content', '')[:200] + '...'
            })
        
        return QuestionResponse(
            answer=answer,
            sources=sources,
            confidence=confidence,
            response_time=time.time() - start_time_req,
            search_results_count=len(search_results)
        )
        
    except Exception as e:
        logger.error(f"Question answering failed: {e}")
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")

@app.get("/sources")
async def get_available_sources():
    """Get list of available documentation sources"""
    try:
        stats = vector_store.get_collection_stats()
        sources = stats.get('sources', {})
        
        return {
            "sources": list(sources.keys()),
            "source_details": sources,
            "total_sources": len(sources)
        }
    except Exception as e:
        logger.error(f"Failed to get sources: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve sources")

@app.get("/sources/{source_name}")
async def get_source_info(source_name: str):
    """Get detailed information about a specific source"""
    try:
        # Search for documents from this source
        results = vector_store.search(
            query="",  # Empty query to get all
            k=10,
            filter_dict={'source': source_name.lower()}
        )
        
        if not results:
            raise HTTPException(status_code=404, detail=f"Source '{source_name}' not found")
        
        # Get unique document types for this source
        doc_types = set()
        sample_docs = []
        
        for result in results:
            metadata = result.get('metadata', {})
            doc_types.add(metadata.get('doc_type', 'general'))
            
            if len(sample_docs) < 5:
                sample_docs.append({
                    'title': metadata.get('title', 'Unknown'),
                    'doc_type': metadata.get('doc_type', 'general'),
                    'url': metadata.get('url', '#')
                })
        
        stats = vector_store.get_collection_stats()
        source_count = stats.get('sources', {}).get(source_name.lower(), 0)
        
        return {
            "source": source_name,
            "total_chunks": source_count,
            "document_types": list(doc_types),
            "sample_documents": sample_docs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get source info: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve source information")

@app.post("/upload-document", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload and process a document (Markdown, CSV, or Text)"""
    try:
        # Check file type
        allowed_extensions = ['md', 'markdown', 'csv', 'txt']
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension not in allowed_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type '{file_extension}'. Allowed: {allowed_extensions}"
            )
        
        logger.info(f"📤 Processing uploaded file: {file.filename}")
        
        # Read file content
        file_content = await file.read()
        
        # Process document
        try:
            from src.ingestion.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            chunks = processor.process_uploaded_file(file_content, file.filename, file_extension)
        except ImportError:
            raise HTTPException(status_code=500, detail="Document processor not available")
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not process the file - no content extracted")
        
        # Add to vector store
        added_count = 0
        failed_count = 0
        
        for i, chunk in enumerate(chunks):
            try:
                doc_id = f"upload_{file.filename}_{i}_{hash(chunk['content']) % 10000}"
                
                # Try different methods to add to vector store
                if hasattr(vector_store, 'add'):
                    vector_store.add(
                        text=chunk['content'],
                        metadata=chunk['metadata'],
                        doc_id=doc_id
                    )
                elif hasattr(vector_store, 'collection'):
                    vector_store.collection.add(
                        documents=[chunk['content']],
                        metadatas=[chunk['metadata']],
                        ids=[doc_id]
                    )
                else:
                    raise Exception("Vector store method not found")
                
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
            total_chunks_now = "unknown"
        
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

@app.get("/upload-info")
async def get_upload_info():
    """Get information about file upload capabilities"""
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
        "current_stats": {
            "total_chunks": vector_store.get_collection_stats().get('total_chunks', 0) if vector_store else 0,
            "sources": len(vector_store.get_collection_stats().get('sources', {})) if vector_store else 0
        }
    }

# Development server runner
def run_server():
    """Run the development server"""
    logger.info("🚀 Starting DocuMentor API development server...")
    uvicorn.run(
        "api_server:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()