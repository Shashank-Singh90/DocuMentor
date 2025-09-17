#!/usr/bin/env python3
"""
DocuMentor API Server - Test Version (No ChromaDB)
"""
import time
import uvicorn
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Import working components (skip ChromaDB)
try:
    from src.generation.ollama_handler import OllamaLLMHandler
    from src.utils.logger import get_logger
    OLLAMA_AVAILABLE = True
except ImportError as e:
    print(f"Warning: {e}")
    OLLAMA_AVAILABLE = False

if OLLAMA_AVAILABLE:
    logger = get_logger(__name__)

# Globals
llm_handler = None
start_time = time.time()

app = FastAPI(title="DocuMentor API - Test Version", version="0.5.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionQuery(BaseModel):
    question: str
    k: int = 5
    temperature: float = 0.4

@app.on_event("startup")
async def startup_event():
    global llm_handler
    
    print("🚀 Starting DocuMentor (Test Mode)...")
    
    if OLLAMA_AVAILABLE:
        try:
            llm_handler = OllamaLLMHandler()
            print("✅ Ollama handler initialized")
        except Exception as e:
            print(f"❌ Ollama initialization failed: {e}")
            llm_handler = None
    else:
        print("⚠️ Ollama handler not available (import failed)")

@app.get("/")
async def root():
    return {
        "message": "DocuMentor API - Test Version", 
        "version": "0.5.0", 
        "status": "running",
        "docs": "/docs",
        "ollama_ready": llm_handler is not None,
        "mode": "test (no ChromaDB)"
    }

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "components": {
            "ollama": "ok" if llm_handler else "not available",
            "vectordb": "disabled (test mode)"
        },
        "uptime": time.time() - start_time
    }

@app.post("/ask")
async def ask_endpoint(query: QuestionQuery):
    """Ask a question - simplified version"""
    if not llm_handler:
        return {
            "answer": "Ollama is not available. This is a test response.",
            "sources": [],
            "question": query.question,
            "mode": "test (no Ollama)"
        }
    
    try:
        prompt = f"Question: {query.question}\n\nAnswer:"
        response = llm_handler.generate(prompt, temperature=query.temperature)
        
        return {
            "answer": response,
            "sources": [],
            "question": query.question,
            "mode": "direct (no vector search)"
        }
    except Exception as e:
        return {
            "answer": f"Error: {str(e)}",
            "sources": [],
            "question": query.question,
            "mode": "error"
        }

@app.get("/stats")
async def stats():
    return {
        "total_chunks": 0,
        "sources": {},
        "total_sources": 0,
        "mode": "test",
        "uptime": time.time() - start_time
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False)
    