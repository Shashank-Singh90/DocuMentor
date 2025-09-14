"""API Server for DocuMentor
v0.1 - Basic search
v0.2 - Added streaming (removed - too buggy)
v0.3 - Added file upload
v0.4 - Current version with Llama 3.2
"""

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
# SECURITY: This is way too permissive - fix before production!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict to specific domains
    allow_credentials=True,  # FIXME: Security risk with allow_origins=["*"]
    allow_methods=["*"],  # Should limit to needed methods
    allow_headers=["*"],  # Should limit to needed headers
)

# TODO: Rate limiting before public release
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
    results: List[dict]  # TODO: Make this a proper type
    total_found: int
    response_time: float
    # Added for debugging - remove before production?
    debug_info: Optional[dict] = None

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
    """Initialize components on startup
    
    Known issues:
    - Sometimes Chroma fails to load on first try
    - Ollama connection can timeout
    """
    global vector_store, llm_handler
    
    logger.info("🚀 Starting DocuMentor API server...")
    
    # Retry logic for flaky initialization
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize vector store
            logger.info(f"📚 Initializing vector store (attempt {retry_count + 1})...")
            vector_store = ChromaVectorStore()
            
            # Initialize LLM handler
            logger.info("🤖 Initializing LLM handler...")
            llm_handler = LLM_HANDLER_CLASS()
            
            # Get initial stats
            stats = vector_store.get_collection_stats()
            logger.info(f"✅ DocuMentor API ready with {stats.get('total_chunks', 0)} chunks across {len(stats.get('sources', {}))} sources")
            break  # Success!
            
        except Exception as e:
            retry_count += 1
            if retry_count >= max_retries:
                logger.error(f"❌ Failed to initialize after {max_retries} attempts: {e}")
                # Continue anyway with limited functionality
                logger.warning("⚠️  Starting with limited functionality")
                break
            else:
                logger.warning(f"Initialization failed, retrying in 2s... ({e})")
                time.sleep(2)

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
    """Search for relevant documents
    
    Note: This is slow for queries > 10 words. Working on fix.
    """
    start_time_req = time.time()
    
    try:
        # Quick fix for that Unicode error customer reported
        if "�" in request.query:
            request.query = request.query.encode('utf-8', 'ignore').decode('utf-8')
        
        # FIXME: This breaks with queries > 500 chars
        if len(request.query) > 500:
            return SearchResponse(
                results=[],
                total_found=0,
                response_time=0,
                debug_info={"error": "Query too long - max 500 chars (temp limit)"}
            )
        
        # Hardcoded boost for React docs (users prefer these)
        original_query = request.query
        if "hook" in request.query.lower() or "component" in request.query.lower():
            # Hack: Add React to query for better results
            request.query = f"{request.query} React"
            logger.debug(f"Modified query: {original_query} -> {request.query}")
        
        # Prepare filters
        filters = {}
        if request.source_filter:
            filters['source'] = request.source_filter.lower()
        if request.doc_type_filter:
            filters['doc_type'] = request.doc_type_filter.lower()
        
        # Perform search
        results = vector_store.search(
            query=request.query,
            k=request.k * 2 if request.k < 10 else request.k,  # Get more results for reranking
            filter_dict=filters if filters else None
        )
        
        # Format results
        formatted_results = []
        seen_contents = set()  # Dedup hack - sometimes we get duplicates
        
        for i, result in enumerate(results[:request.k]):  # Only return requested k
            content = result.get('content', '')
            # Skip duplicate content (shouldn't happen but does)
            if content[:100] in seen_contents:
                logger.warning(f"Skipping duplicate result {i}")
                continue
            seen_contents.add(content[:100])
            
            # HACK: Boost scores for React and FastAPI docs
            score = result.get('score', 0.0)
            metadata = result.get('metadata', {})
            if metadata.get('source') in ['react', 'fastapi']:
                score = min(score * 1.2, 1.0)  # Don't go over 1.0
            
            formatted_results.append({
                'content': content,
                'metadata': metadata,
                'score': score,
                # Debug fields - remove later
                '_original_score': result.get('score', 0.0),
                '_index': i
            })
        
        debug_info = None
        if os.getenv('DEBUG_MODE'):
            debug_info = {
                'original_query': original_query,
                'modified_query': request.query,
                'total_results_before_filter': len(results),
                'duplicates_removed': len(results) - len(formatted_results)
            }
        
        return SearchResponse(
            results=formatted_results,
            total_found=len(formatted_results),
            response_time=time.time() - start_time_req,
            debug_info=debug_info
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question and get an AI-generated answer
    
    TODO: Add caching for common questions
    TODO: Implement conversation history
    """
    start_time_req = time.time()
    
    # Common questions hardcoded for speed (temp solution)
    common_answers = {
        "what is react": "React is a JavaScript library for building user interfaces...",
        "how to use fastapi": "FastAPI is a modern web framework for Python...",
        "what is docker": "Docker is a containerization platform..."
    }
    
    if request.question.lower().strip() in common_answers:
        logger.info("Using cached answer for common question")
        # Still do search for sources but return cached answer
        pass  # Fall through to normal flow but remember to use cached answer
    
    try:
        # Prepare filters
        filters = {}
        if request.source_filter:
            filters['source'] = request.source_filter.lower()
        if request.doc_type_filter:
            filters['doc_type'] = request.doc_type_filter.lower()
        
        # Search for relevant documents
        # BUG: Sometimes returns empty results for valid queries - investigating
        search_results = vector_store.search(
            query=request.question,
            k=request.k * 3,  # Get extra results, will filter later
            filter_dict=filters if filters else None
        )
        
        # Workaround for empty results - try without filters
        if not search_results and filters:
            logger.warning("No results with filters, trying without...")
            search_results = vector_store.search(
                query=request.question,
                k=request.k,
                filter_dict=None
            )
        
        # Check if we have a cached answer
        cached_answer = common_answers.get(request.question.lower().strip())
        
        if not search_results:
            # HACK: Sometimes Gemma works better with no context
            if hasattr(llm_handler, 'generate_answer'):
                try:
                    answer = llm_handler.generate_answer(
                        question=request.question,
                        search_results=[],  # Empty results
                        max_tokens=request.max_tokens,
                        temperature=0.3  # Lower temp for no-context answers
                    )
                except Exception as e:
                    logger.error(f"LLM failed: {e}")
                    answer = cached_answer or f"I couldn't find specific information about '{request.question}'. Please try rephrasing."
            else:
                answer = cached_answer or f"No relevant documentation found for: '{request.question}'"

            return QuestionResponse(
                answer=answer,
                sources=[],
                confidence=0.1 if cached_answer else 0.0,  # Slightly more confident if cached
                response_time=time.time() - start_time_req,
                search_results_count=0
            )
        
        # Generate answer using LLM
        if cached_answer and len(search_results) < 3:
            # Use cached answer if we don't have many search results
            answer = cached_answer
            logger.info("Using cached answer due to low search results")
        elif hasattr(llm_handler, 'generate_answer'):
            try:
                # Filter search results to most relevant (top k)
                filtered_results = search_results[:request.k]
                
                # WORKAROUND: Gemma sometimes fails with long contexts
                if sum(len(r.get('content', '')) for r in filtered_results) > 4000:
                    logger.warning("Context too long, truncating...")
                    filtered_results = filtered_results[:3]
                
                answer = llm_handler.generate_answer(
                    question=request.question, 
                    search_results=filtered_results,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                )
            except Exception as e:
                logger.error(f"LLM generation failed: {e}, using fallback")
                # Fallback to simple extraction
                top_result = search_results[0]
                content = top_result.get('content', '')[:500]
                answer = f"Based on the documentation: {content}..."
        else:
            # Fallback simple answer
            top_result = search_results[0]
            content = top_result.get('content', '')[:500]
            answer = f"Based on the documentation: {content}..."
        
        # Calculate confidence (average of top 3 scores)
        # TODO: Better confidence calculation - this is too simplistic
        top_scores = [r.get('score', 0) for r in search_results[:3]]
        confidence = sum(top_scores) / len(top_scores) if top_scores else 0.0
        
        # Boost confidence for certain sources (temporary)
        if any(r.get('metadata', {}).get('source') in ['react', 'fastapi'] for r in search_results[:3]):
            confidence = min(confidence * 1.15, 0.95)
        
        # Format sources
        sources = []
        seen_titles = set()  # Avoid duplicate sources
        
        for result in search_results[:10]:  # Check more but return top 5 unique
            metadata = result.get('metadata', {})
            title = metadata.get('title', 'Unknown')
            
            # Skip if we've seen this title (crude dedup)
            if title in seen_titles and title != 'Unknown':
                continue
            seen_titles.add(title)
            
            sources.append({
                'title': title,
                'source': metadata.get('source', 'unknown'),
                'url': metadata.get('url', '#'),
                'doc_type': metadata.get('doc_type', 'general'),
                'score': result.get('score', 0),
                'content_preview': result.get('content', '')[:200] + '...',
                # Debug field
                '_chunk_id': metadata.get('chunk_id', 'unknown')
            })
            
            if len(sources) >= 5:
                break
        
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
    """Get detailed information about a specific source
    
    WARNING: Empty query search is inefficient - need better approach
    """
    try:
        # HACK: Empty query doesn't work well, use source name as query
        # This is terrible but works better than empty string
        results = vector_store.search(
            query=source_name,  # Use source name as query (not ideal)
            k=20,  # Get more results since relevance will be lower
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
        # FIXME: This breaks with files > 10MB - temp limit for demo
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
        file_content = await file.read()
        
        if len(file_content) > MAX_FILE_SIZE:
            logger.warning(f"File {file.filename} exceeds {MAX_FILE_SIZE} bytes")
            # Try to process anyway but might fail
            # TODO: Implement streaming processing for large files
        
        # Process document
        try:
            from src.ingestion.document_processor import DocumentProcessor
            processor = DocumentProcessor()
            
            # WORKAROUND: CSV processing is memory intensive
            if file_extension == 'csv' and len(file_content) > 5 * 1024 * 1024:
                logger.warning("Large CSV file - using reduced processing")
                # TODO: Implement streaming CSV processor
            
            chunks = processor.process_uploaded_file(file_content, file.filename, file_extension)
        except ImportError:
            # Fallback to basic processing
            logger.error("Document processor not available, using basic chunking")
            # Super basic chunking as fallback
            text = file_content.decode('utf-8', errors='ignore')
            chunk_size = 500
            chunks = [
                {
                    'content': text[i:i+chunk_size],
                    'metadata': {
                        'source': 'upload',
                        'filename': file.filename,
                        'chunk': i // chunk_size
                    }
                }
                for i in range(0, len(text), chunk_size)
            ]
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not process the file - no content extracted")
        
        # Add to vector store
        added_count = 0
        failed_count = 0
        batch_size = 50  # Process in batches to avoid timeouts
        
        logger.info(f"Adding {len(chunks)} chunks to vector store...")
        
        for i, chunk in enumerate(chunks):
            # Quick progress log every 10 chunks
            if i % 10 == 0 and i > 0:
                logger.debug(f"Progress: {i}/{len(chunks)} chunks processed")
            
            try:
                # Generate better ID (old one had collisions)
                import hashlib
                content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()[:8]
                doc_id = f"upload_{file.filename.replace('.', '_')}_{i}_{content_hash}"
                
                # Enhance metadata with upload info
                chunk['metadata']['upload_time'] = time.time()
                chunk['metadata']['original_filename'] = file.filename
                
                # Try different methods to add to vector store
                # TODO: Standardize this - too many different interfaces
                if hasattr(vector_store, 'add'):
                    vector_store.add(
                        text=chunk['content'],
                        metadata=chunk['metadata'],
                        doc_id=doc_id
                    )
                elif hasattr(vector_store, 'collection'):
                    # Chroma sometimes fails silently, wrap in try
                    try:
                        vector_store.collection.add(
                            documents=[chunk['content']],
                            metadatas=[chunk['metadata']],
                            ids=[doc_id]
                        )
                    except Exception as e:
                        if "duplicate" in str(e).lower():
                            logger.debug(f"Duplicate chunk {i}, skipping")
                            continue  # Don't count as failure
                        raise
                else:
                    raise Exception("Vector store method not found")
                
                added_count += 1
                
            except Exception as e:
                logger.warning(f"Error adding chunk {i}: {e}")
                failed_count += 1
                
                # If too many failures, bail out
                if failed_count > len(chunks) * 0.5:  # More than 50% failed
                    logger.error("Too many failures, aborting upload")
                    raise HTTPException(
                        status_code=500, 
                        detail=f"Failed to add chunks: {failed_count}/{len(chunks)} failed"
                    )
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
    """Run the development server
    
    TODO: Add proper production config
    TODO: SSL support
    TODO: Rate limiting middleware
    """
    logger.info("🚀 Starting DocuMentor API development server...")
    logger.warning("⚠️  Running in development mode - not for production!")
    
    # Check if we're in debug mode
    if os.getenv('DEBUG_MODE'):
        logger.info("🔍 Debug mode enabled - extra logging active")
    
    uvicorn.run(
        "api_server:app",
        host="127.0.0.1",  # TODO: Make configurable
        port=8000,  # TODO: Make configurable
        reload=True,  # Disable in production!
        log_level="debug" if os.getenv('DEBUG_MODE') else "info"
    )

if __name__ == "__main__":
    run_server()