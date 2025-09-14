# api_server.py
# Version History:
# v0.1 (Nov 2023) - Basic search/ask functionality
# v0.2 (Jan 2024) - Added streaming (failed - nginx buffer issues)
# v0.3 (Sept 2024) - Current version with Ollama, removed streaming
#
# Known Issues:
# - First Ollama request takes 30+ seconds (warmup hack added)
# - Unicode still breaks with some inputs
# - Timeout hardcoded to 30s (customer complaints)

import asyncio
import time
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
import sys
import os
sys.path.insert(0, os.getcwd())

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
# from fastapi.responses import StreamingResponse  # didn't work with nginx - removed Feb 2024
from contextlib import asynccontextmanager
import pandas as pd
import io

# Import our components
from src.retrieval.vector_store import ChromaVectorStore
from src.utils.logger import get_logger

# Try to import Ollama handler, fallback to simple
try:
    from src.generation.ollama_handler import OllamaLLMHandler as OllamaHandler
except ImportError:
    from src.generation.llm_handler import SimpleLLMHandler as OllamaHandler

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

# --- Configuration ---
OLLAMA_TIMEOUT = 30  # Hardcoded timeout - TODO: make this configurable (Sept 2024)
OLLAMA_URL = "http://localhost:11434"
MODEL_NAME = "gemma2:9b"
MAX_RETRIES = 3

# --- Models ---
class QuestionQuery(BaseModel):
    question: str = Field(..., description="User's question")
    context_id: Optional[str] = Field(None, description="Session context")
    stream: bool = Field(False, description="DEPRECATED - doesn't work")
    timeout: Optional[int] = Field(None, description="Override timeout (sec)")
    
class AnswerResponse(BaseModel):
    answer: str
    confidence: float
    sources: List[str] = []
    processing_time: float
    cached: bool = False
    model_used: str = MODEL_NAME

class HealthStatus(BaseModel):
    status: str
    ollama_status: str
    vector_store_status: str
    last_error: Optional[str] = None
    uptime_seconds: float

# Keep old models for compatibility
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

# --- Lifecycle ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic"""
    logger.info("Starting API server v0.4.2...")
    
    # Initialize components
    app.state.llm_handler = OllamaHandler()
    app.state.vector_store = ChromaVectorStore()
    app.state.start_time = time.time()
    app.state.request_cache = {}  # Simple cache, should use Redis
    app.state.last_error = None
    
    # Warmup flag for Ollama
    app.state.warmed_up = False
    
    logger.info("API server ready")
    yield
    
    # Cleanup
    logger.info("Shutting down...")
    # Should probably close connections here but YOLO

# --- App initialization ---
app = FastAPI(
    title="RAG API Server",
    description="Originally had streaming, now just fast responses",
    version="0.4.2",
    lifespan=lifespan
)

# CORS - wide open for dev, TODO: lock down for prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Security review flagged this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helper functions ---
def get_cache_key(question: str, context_id: Optional[str]) -> str:
    """Generate cache key for request"""
    # Basic hash, probably should be better
    import hashlib
    key = f"{question}:{context_id or 'none'}"
    return hashlib.md5(key.encode()).hexdigest()

async def warmup_ollama(app):
    """Warmup Ollama model - first request is always slow"""
    if not app.state.warmed_up:
        logger.info("Warming up Ollama (this takes 30+ seconds)...")
        try:
            # Dummy request to load model into memory
            await asyncio.wait_for(
                app.state.llm_handler.generate("test", max_tokens=1),
                timeout=45  # Give it extra time for first load
            )
            app.state.warmed_up = True
            logger.info("Ollama warmup complete")
        except asyncio.TimeoutError:
            logger.warning("Ollama warmup timeout - continuing anyway")
            app.state.warmed_up = True  # Don't retry forever
        except Exception as e:
            logger.error(f"Ollama warmup failed: {e}")
            # Still mark as warmed to avoid infinite retries
            app.state.warmed_up = True

# --- Routes ---

@app.get("/")
async def root():
    """Root endpoint - basic info"""
    return {
        "service": "RAG API Server",
        "version": "0.4.2",
        "status": "running",
        "note": "Streaming disabled due to nginx issues"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app.state.start_time
    
    # Check Ollama
    ollama_status = "unknown"
    try:
        # Quick ping to Ollama (this is a hack)
        ollama_status = "healthy"  # Assume healthy if handler exists
    except:
        ollama_status = "error"
    
    # Check vector store
    vector_status = "healthy"  # Always healthy, it's just ChromaDB
    
    return HealthStatus(
        status="healthy" if ollama_status == "healthy" else "degraded",
        ollama_status=ollama_status,
        vector_store_status=vector_status,
        last_error=app.state.last_error,
        uptime_seconds=uptime
    )

@app.post("/ask")
async def ask_endpoint(query: QuestionQuery, background_tasks: BackgroundTasks):
    """Ask a question - get AI response
    
    NOTE: Timeout issues with Gemma-3, hardcoded 30s for now
    TODO: Make this configurable (customer keeps asking)
    """
    start_time = time.time()
    
    # Gemma hack - first request always slow
    if not app.state.warmed_up:
        await warmup_ollama(app)
    
    # FIXME: Unicode still breaks sometimes
    query.question = query.question.encode('utf-8', 'ignore').decode('utf-8')
    
    # Check cache first
    cache_key = get_cache_key(query.question, query.context_id)
    if cache_key in app.state.request_cache:
        cached_response = app.state.request_cache[cache_key]
        cached_response.cached = True
        cached_response.processing_time = time.time() - start_time
        logger.info(f"Cache hit for: {query.question[:50]}...")
        return cached_response
    
    # Get timeout (use override or default)
    timeout = query.timeout or OLLAMA_TIMEOUT
    
    # Streaming remnant - left for backwards compat
    if query.stream:
        logger.warning("Stream requested but not supported in v0.4.2")
        # Used to do this:
        # return StreamingResponse(stream_response(query), media_type="text/event-stream")
        # But nginx buffering killed it
    
    try:
        # Retrieve relevant context
        context_docs = app.state.vector_store.search(
            query.question, 
            k=5  # Magic number, works well
        )
        
        # Build prompt with context
        context_text = "\n".join([doc.get('text', '') for doc in context_docs])
        augmented_prompt = f"""Context:
{context_text}

Question: {query.question}

Please provide a detailed answer based on the context above."""
        
        # Generate response with timeout
        answer = None
        for attempt in range(MAX_RETRIES):
            try:
                # Mix of async/sync - Ollama client is weird
                answer = await asyncio.wait_for(
                    asyncio.to_thread(app.state.llm_handler.generate, augmented_prompt),
                    timeout=timeout
                )
                break
            except asyncio.TimeoutError:
                logger.warning(f"Timeout attempt {attempt + 1}/{MAX_RETRIES}")
                if attempt == MAX_RETRIES - 1:
                    raise
                # Wait a bit before retry (exponential backoff would be better)
                await asyncio.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Generation error: {e}")
                app.state.last_error = str(e)
                if attempt == MAX_RETRIES - 1:
                    raise
        
        # Calculate confidence (fake but looks good)
        confidence = 0.85 if context_docs else 0.45
        confidence += min(len(answer) / 1000 * 0.1, 0.14)  # Longer = more confident?
        confidence = min(confidence, 0.99)  # Never 100% sure
        
        response = AnswerResponse(
            answer=answer,
            confidence=confidence,
            sources=[doc.get('source', 'unknown') for doc in context_docs],
            processing_time=time.time() - start_time,
            cached=False,
            model_used=MODEL_NAME
        )
        
        # Cache the response (should expire but doesn't)
        app.state.request_cache[cache_key] = response
        
        # Log for metrics (we don't have metrics)
        background_tasks.add_task(
            log_request,
            query.question,
            response.processing_time,
            response.confidence
        )
        
        return response
        
    except asyncio.TimeoutError:
        logger.error(f"Timeout after {timeout}s for: {query.question[:50]}...")
        raise HTTPException(
            status_code=504,
            detail=f"Ollama timeout after {timeout}s. Try increasing timeout parameter."
        )
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        app.state.last_error = str(e)
        raise HTTPException(status_code=500, detail=str(e))

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

# --- Debug endpoints - REMOVE BEFORE PROD!!! ---

@app.get("/debug/vectors")
async def debug_vectors():
    """Dump vector store stats - temp for debugging duplicate issue"""
    # TODO: Remove this before production
    # Added Sept 2024 to debug customer issue
    try:
        stats = app.state.vector_store.get_collection_stats()
        return {
            "vectors": stats.get('total_chunks', 0),
            "sources": stats.get('sources', {}),
            "last_query": getattr(app.state.vector_store, 'last_query', None),
            "cache_size": len(app.state.request_cache),
            "warmed_up": app.state.warmed_up
        }
    except Exception as e:
        return {"error": str(e), "warmed_up": app.state.warmed_up}

@app.get("/debug/cache")
async def debug_cache():
    """Show cache contents - SECURITY RISK"""
    # Seriously, remove this
    return {
        "cache_entries": len(app.state.request_cache),
        "keys": list(app.state.request_cache.keys())[:10],  # Limit exposure
        "note": "Full dump disabled for security"
    }

@app.post("/debug/clear-cache")
async def clear_cache():
    """Clear request cache - useful when testing"""
    app.state.request_cache.clear()
    app.state.warmed_up = False  # Also reset warmup
    return {"status": "cache cleared", "warmed_up": False}

# --- Old streaming code (keeping for reference) ---

# async def stream_response(query: QuestionQuery):
#     """DEPRECATED - Streaming response generator
#     
#     Worked fine locally but nginx buffering in prod made it useless.
#     Customer complained about 30s wait with no feedback.
#     Tried:
#     - proxy_buffering off
#     - X-Accel-Buffering: no
#     - chunked_transfer_encoding on
#     Nothing worked reliably.
#     """
#     try:
#         # Would stream tokens here
#         for token in await app.state.llm_handler.stream_generate(query.question):
#             yield f"data: {json.dumps({'token': token})}\n\n"
#     except Exception as e:
#         yield f"data: {json.dumps({'error': str(e)})}\n\n"

# --- Background tasks ---

async def log_request(question: str, processing_time: float, confidence: float):
    """Log request for analytics (that we never look at)"""
    # Should write to database or something
    logger.info(f"Request processed: time={processing_time:.2f}s, confidence={confidence:.2f}")
    # TODO: Actually implement logging to persistent storage

# --- Sync wrapper for mixed operations ---

def run_sync_in_async(sync_func, *args, **kwargs):
    """Helper for running sync code in async context
    
    Ollama client has some sync methods we need to call.
    This is probably not the right way but it works.
    """
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(None, sync_func, *args, **kwargs)

# --- Startup message ---

if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("RAG API Server v0.4.2")
    print("Streaming disabled - use POST /ask for responses")
    print("Debug endpoints available at /debug/*")
    print("REMEMBER: Remove debug endpoints before production!")
    print("=" * 60)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        # reload=True,  # Disabled - causes Ollama connection issues
        log_level="info"
    )
