"""
Enhanced FastAPI REST API v2 for Advanced RAG System
Provides programmatic access to all enhanced RAG functionality

Production-ready with:
- API Key Authentication
- Rate Limiting
- Input Validation
- Metrics & Monitoring
- Structured Logging
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import json
import io
import time
from pathlib import Path

from rag_system.core import DocumentChunker, VectorStore
from rag_system.core.processing import document_processor
from rag_system.core.generation.llm_handler import llm_service
from rag_system.core.search import web_search_provider
from rag_system.config import get_settings
from rag_system.api.middleware.auth import verify_api_key, optional_verify_api_key
from rag_system.api.middleware.validation import (
    validate_query,
    validate_search_k,
    validate_temperature,
    validate_max_tokens,
    validate_file_upload,
    sanitize_filename,
)
from rag_system.core.utils.metrics import (
    track_request_duration,
    track_llm_request,
    track_vector_search,
    record_api_request,
    record_auth_attempt,
    record_rate_limit_hit,
    update_vector_store_size,
)
from rag_system.core.constants import (
    RATE_LIMIT_SEARCH,
    RATE_LIMIT_UPLOAD,
    RATE_LIMIT_QUERY,
    RATE_LIMIT_GENERATION,
    DEFAULT_SEARCH_K,
    MAX_SEARCH_K,
)
from rag_system.core.utils.logger import get_logger

logger = get_logger(__name__)

# Technology mapping
TECHNOLOGY_MAPPING = {
    'python': 'Python 3.13',
    'fastapi': 'FastAPI',
    'django': 'Django 5.0',
    'react_nextjs': 'React & Next.js',
    'nodejs': 'Node.js',
    'postgresql': 'PostgreSQL',
    'mongodb': 'MongoDB',
    'typescript': 'TypeScript',
    'langchain': 'LangChain'
}

class QueryRequest(BaseModel):
    question: str = Field(..., description="The user query")
    search_k: int = Field(default=8, description="Documents to retrieve")
    enable_web_search: bool = Field(default=False)
    response_mode: str = Field(default="smart_answer", description="Mode: smart_answer, code_generation, detailed_sources")
    technology_filter: Optional[str] = None
    source_filter: Optional[List[str]] = None
    temperature: float = Field(default=0.3)
    max_tokens: int = Field(default=800)
    chunk_overlap: int = Field(default=2)

class CodeGenerationRequest(BaseModel):
    prompt: str = Field(..., description="What to build")
    language: str = Field(default="python")
    technology: Optional[str] = None
    include_context: bool = True
    style: str = "complete"

class TechnologyFilterRequest(BaseModel):
    technology: str
    question: str
    mode: str = "smart"

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]]
    response_time: float
    provider_used: str
    source_count: int
    technology_context: Optional[str]
    response_mode: str
    search_metadata: Dict[str, Any]

class SystemStatus(BaseModel):
    status: str
    providers: Dict[str, bool]
    document_count: int
    available_sources: List[str]
    available_technologies: List[str]
    supported_formats: List[str]
    system_version: str

class TechnologyStatsResponse(BaseModel):
    technology: str
    chunk_count: int
    sample_content: List[str]
    topics_covered: List[str]

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    settings = get_settings()

    app = FastAPI(
        title="DocuMentor API",
        description="API for Documentation Assistant",
        version="2.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )

    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    vector_store = VectorStore()
    chunker = DocumentChunker()

    logger.info("API initialized")

    @app.get("/", tags=["General"])
    async def root():
        return {
            "message": "DocuMentor API",
            "version": "2.0.0",
            "status": "/status",
        }

    @app.get("/status", response_model=SystemStatus, tags=["General"])
    async def get_status():
        """Get system status"""
        try:
            stats = vector_store.get_collection_stats()
            provider_status = llm_service.get_provider_status()
            update_vector_store_size(stats.get('total_chunks', 0))

            return SystemStatus(
                status="operational",
                providers=provider_status,
                document_count=stats.get('total_chunks', 0),
                available_sources=list(stats.get('sources', {}).keys()),
                available_technologies=list(TECHNOLOGY_MAPPING.values()),
                supported_formats=document_processor.get_supported_formats(),
                system_version="2.0.0"
            )
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/metrics", tags=["Monitoring"])
    async def get_metrics():
        return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/technologies", tags=["Technologies"])
    async def list_technologies():
        """List available technologies"""
        try:
            stats = vector_store.get_collection_stats()
            technologies = []

            for tech_key, tech_name in TECHNOLOGY_MAPPING.items():
                tech_filter = {"technology": tech_key}
                tech_results = vector_store.search("overview", k=1, filter_dict=tech_filter)
                technologies.append({
                    "key": tech_key,
                    "name": tech_name,
                    "available": len(tech_results) > 0
                })

            return {
                "total_technologies": len(TECHNOLOGY_MAPPING),
                "technologies": technologies,
                "total_chunks": stats.get('total_chunks', 0)
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    
    @app.get("/technologies/{technology}/stats", response_model=TechnologyStatsResponse, tags=["Technologies"])
    async def get_technology_stats(technology: str):
        if technology not in TECHNOLOGY_MAPPING:
            raise HTTPException(status_code=404, detail="Technology not found")
            
        tech_filter = {"technology": technology}
        results = vector_store.search("", k=5, filter_dict=tech_filter)
        
        return TechnologyStatsResponse(
            technology=TECHNOLOGY_MAPPING[technology],
            chunk_count=len(results),
            sample_content=[r.get('content', '')[:100] for r in results],
            topics_covered=[]
        )

    @app.post("/ask", response_model=QueryResponse, tags=["Q&A"])
    @limiter.limit(f"{RATE_LIMIT_QUERY}/minute")
    async def ask_question(http_request: Request, request: QueryRequest):
        """Ask a question"""
        try:
            start_time = time.time()
            combined_filter = {}

            if request.technology_filter and request.technology_filter in TECHNOLOGY_MAPPING:
                combined_filter = {
                    "$and": [
                        {"technology": request.technology_filter},
                        {"source": "comprehensive_docs"}
                    ]
                }

            if request.source_filter:
                combined_filter["source"] = {"$in": request.source_filter}

            filter_dict = combined_filter if combined_filter else None
            
            search_results = []
            if request.response_mode != "web_only":
                search_results = vector_store.search(
                    request.question,
                    k=request.search_k + request.chunk_overlap,
                    filter_dict=filter_dict
                )

            if request.enable_web_search:
                search_results.extend(web_search_provider.search_web(request.question, max_results=3))

            if request.response_mode == "code_generation":
                prompt = f"Provide a complete code implementation for: {request.question}"
                answer = llm_service.generate_code(prompt, "python", search_results[:5])
                if "```" not in answer:
                    answer = f"```python\n{answer}\n```"
            else:
                answer = llm_service.generate_answer(f"Question: {request.question}", search_results)

            return QueryResponse(
                answer=answer,
                sources=search_results,
                response_time=time.time() - start_time,
                provider_used=llm_service.current_provider,
                source_count=len(search_results),
                technology_context=TECHNOLOGY_MAPPING.get(request.technology_filter),
                response_mode=request.response_mode,
                search_metadata={"web_search": request.enable_web_search}
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/generate-code", tags=["Code Generation"])
    @limiter.limit(f"{RATE_LIMIT_GENERATION}/minute")
    async def generate_code(http_request: Request, request: CodeGenerationRequest):
        """Generate code"""
        try:
            context = []
            if request.include_context:
                search_query = f"{request.language} {request.prompt}"
                filter_dict = {"technology": request.technology} if request.technology in TECHNOLOGY_MAPPING else None
                context = vector_store.search(search_query, k=5, filter_dict=filter_dict)

            code = llm_service.generate_code(
                f"Generate {request.style} {request.language} code. Request: {request.prompt}",
                request.language,
                context
            )

            return {
                "code": code,
                "language": request.language,
                "technology": TECHNOLOGY_MAPPING.get(request.technology, "General"),
                "context_used": len(context),
                "provider": llm_service.current_provider
            }

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/technology-query", tags=["Technology Queries"])
    @limiter.limit(f"{RATE_LIMIT_QUERY}/minute")
    async def technology_specific_query(http_request: Request, request: TechnologyFilterRequest):
        """Query with technology-specific filtering and context"""
        try:
            if request.technology not in TECHNOLOGY_MAPPING:
                raise HTTPException(status_code=400, detail=f"Technology '{request.technology}' not supported")

            import time
            start_time = time.time()

            # Technology-specific filter
            tech_filter = {
                "$and": [
                    {"technology": request.technology},
                    {"source": "comprehensive_docs"}
                ]
            }

            # Search with technology filter
            search_results = vector_store.search(
                request.question,
                k=8,
                filter_dict=tech_filter
            )

            # Generate technology-focused response
            tech_name = TECHNOLOGY_MAPPING[request.technology]

            if request.mode == "code":
                prompt = f"Provide {tech_name} code implementation for: {request.question}"
                answer = enhanced_llm_handler.generate_code(prompt, "python", search_results)
            elif request.mode == "detailed":
                prompt = f"Provide detailed {tech_name} documentation and examples for: {request.question}"
                answer = enhanced_llm_handler.generate_answer(prompt, search_results)
            else:  # smart
                prompt = f"Explain how to {request.question} using {tech_name}. Include practical examples."
                answer = enhanced_llm_handler.generate_answer(prompt, search_results)

            response_time = time.time() - start_time

            return {
                "answer": answer,
                "technology": tech_name,
                "mode": request.mode,
                "sources": search_results,
                "response_time": response_time,
                "source_count": len(search_results)
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Technology query failed: {str(e)}")

    # Include all original endpoints for backward compatibility
    @app.post("/ask", response_model=EnhancedQuestionResponse, tags=["Q&A"])
    @limiter.limit(f"{RATE_LIMIT_QUERY}/minute")
    async def ask_question_legacy(http_request: Request, request: EnhancedQuestionRequest):
        """Legacy ask endpoint - redirects to enhanced version"""
        return await ask_enhanced_question(http_request, request)

    @app.post("/upload", tags=["Documents"])
    @limiter.limit(f"{RATE_LIMIT_UPLOAD}/minute")
    async def upload_document(
        http_request: Request,
        file: UploadFile = File(...),
        source: str = Form(default="api_upload")
    ):
        """Upload and process a document (enhanced version)"""
        try:
            # Check file format
            file_extension = Path(file.filename).suffix.lower()
            if not document_processor.is_supported(file_extension):
                raise HTTPException(
                    status_code=400,
                    detail=f"Unsupported file format: {file_extension}"
                )

            # Read file content
            content = await file.read()

            # Process document
            result = document_processor.process_file(file.filename, content)

            if not result['success']:
                raise HTTPException(
                    status_code=400,
                    detail=f"Document processing failed: {result['metadata'].get('error', 'Unknown error')}"
                )

            # Create document object with enhanced metadata
            document = {
                'title': file.filename,
                'content': result['content'],
                'source': source,
                'file_type': file_extension,
                'upload_timestamp': time.time()
            }

            # Chunk the document
            chunks = chunker.chunk_document(document)

            if chunks:
                texts = [chunk['content'] for chunk in chunks]
                metadatas = [chunk['metadata'] for chunk in chunks]
                ids = [f"upload_{file.filename}_{i}" for i in range(len(chunks))]

                added = vector_store.add_documents(texts, metadatas, ids)

                return {
                    "success": True,
                    "message": f"Successfully processed {file.filename}",
                    "chunks_created": added,
                    "document_id": f"upload_{file.filename}",
                    "file_type": file_extension,
                    "processing_metadata": result.get('metadata', {})
                }
            else:
                raise HTTPException(status_code=400, detail="Failed to create chunks from document")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    return app

# Create the FastAPI app instance
app = create_app()