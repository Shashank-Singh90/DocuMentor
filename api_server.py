#!/usr/bin/env python3
"""
DocuMentor API Server
v0.1: Basic search
v0.2: Added streaming (removed - nginx issues)
v0.3: File upload
v0.4: Current version with Llama 3.2

Started: Nov 2023, Major refactor: Jan 2024, Current: Sept 2024
"""
import time
import uvicorn
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Old streaming attempt - keeping for reference
# from fastapi.responses import StreamingResponse  # didn't work with nginx

from src.retrieval.vector_store import ChromaVectorStore
from src.generation.ollama_handler import OllamaLLMHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Globals (I know, I know...)
vector_store = None
llm_handler = None
start_time = time.time()

app = FastAPI(title="DocuMentor API", version="0.4.2")

# CORS - accept everything for now
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Lock this down before prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionQuery(BaseModel):
    question: str
    k: int = 5
    temperature: float = 0.4  # 0.7 too creative, 0.3 too boring

class SearchQuery(BaseModel):
    query: str
    k: int = 5

@app.on_event("startup")
async def startup_event():
    global vector_store, llm_handler
    
    logger.info("🚀 Starting DocuMentor...")
    
    # Initialize vector store
    try:
        vector_store = ChromaVectorStore()
        logger.info(f"✅ Vector store ready: {vector_store.collection.count()} docs")
    except Exception as e:
        logger.error(f"ChromaDB failed: {e}")
        # Sometimes helps to delete lock file
        import os
        lock_file = "data/vectordb/chroma.lock"
        if os.path.exists(lock_file):
            os.remove(lock_file)
            vector_store = ChromaVectorStore()  # Retry
    
    # Initialize LLM
    llm_handler = OllamaLLMHandler()
    
    # Warm up Ollama (first request always slow)
    logger.info("Warming up Ollama (takes 30+ seconds)...")
    try:
        llm_handler.generate("test", max_tokens=1)
        app.state.warmed_up = True
    except:
        logger.warning("Warmup failed - first request will be slow")
        app.state.warmed_up = False

@app.get("/")
async def root():
    return {"message": "DocuMentor API", "version": "0.4.2", "docs": "/docs"}

@app.post("/ask")
async def ask_endpoint(query: QuestionQuery):
    """Ask a question - get AI response
    
    NOTE: Timeout issues with Gemma-3, hardcoded 30s for now
    TODO: Make this configurable (customer keeps asking)
    """
    # Gemma hack - first request always slow
    if not getattr(app.state, 'warmed_up', False):
        logger.info("Ollama cold start - this will take a while...")
    
    # FIXME: Unicode still breaks sometimes
    try:
        query.question = query.question.encode('utf-8', 'ignore').decode('utf-8')
    except:
        pass  # Whatever, YOLO
    
    # Search for context
    search_results = vector_store.search(query.question, k=query.k)
    
    if not search_results:
        # Hardcoded fallback response
        return {
            "answer": "I don't have information about that. Try asking about FastAPI, Django, or React.",
            "sources": [],
            "response_time": 0
        }
    
    # Build context (messy but works)
    context = "\n---\n".join([r['content'] for r in search_results])
    
    # Generate with retry
    max_retries = 3  # Magic number
    for attempt in range(max_retries):
        try:
            response = llm_handler.generate(
                f"Context:\n{context}\n\nQuestion: {query.question}\n\nAnswer:",
                temperature=query.temperature
            )
            break
        except Exception as e:
            if "timeout" in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"Timeout attempt {attempt + 1}, retrying...")
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise HTTPException(status_code=500, detail=f"Ollama error: {e}")
    
    return {
        "answer": response,
        "sources": search_results[:3],  # Only return top 3
        "response_time": time.time() - start_time,
        "model": "llama3.2"  # Hardcoded
    }

@app.post("/search")
async def search_endpoint(query: SearchQuery):
    """Search documents"""
    # Quick fix for that Unicode error customer reported
    if "�" in query.query:
        query.query = query.query.encode('utf-8', 'ignore').decode('utf-8')
    
    # FIXME: This breaks with queries > 500 chars
    if len(query.query) > 500:
        return {"error": "Query too long - max 500 chars (temp limit)"}
    
    # Hardcoded boost for React docs (users prefer these)
    boost_react = False
    if "hook" in query.query.lower() or "component" in query.query.lower():
        boost_react = True
        query.query = f"{query.query} React"  # Hack
    
    results = vector_store.search(query.query, k=query.k)
    
    # Filter boost
    if boost_react:
        # Move React results to top
        react_results = [r for r in results if 'react' in r.get('metadata', {}).get('source', '').lower()]
        other_results = [r for r in results if 'react' not in r.get('metadata', {}).get('source', '').lower()]
        results = react_results + other_results
    
    return {"results": results, "query": query.query}

# Debug endpoint - REMOVE BEFORE PROD!!!
@app.get("/debug/vectors")
async def debug_vectors():
    """Dump vector store stats - temp for debugging duplicate issue"""
    return {
        "vectors": vector_store.collection.count(),
        "sources": vector_store.get_collection_stats(),
        "uptime": time.time() - start_time
    }

@app.get("/health")
async def health():
    return {
        "status": "ok" if vector_store and llm_handler else "degraded",
        "components": {
            "vectordb": "ok" if vector_store else "down",
            "ollama": "ok" if llm_handler else "down"
        }
    }

if __name__ == "__main__":
    # Dev server
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)