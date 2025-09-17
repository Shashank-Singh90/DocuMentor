#!/usr/bin/env python3
"""
DocuMentor API Server - Python 3.11
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="DocuMentor API",
    description="AI-Powered Documentation Assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "DocuMentor API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "python_version": "3.11.9"}

if __name__ == "__main__":
    print("🚀 Starting DocuMentor API Server...")
    print("📊 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)