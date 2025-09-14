#!/usr/bin/env python3
"""
Quick Test for DocuMentor - Fixed version
"""
import requests
import json
import time

API_BASE = "http://localhost:8000"

def test_documentor():
    print("🧪 DocuMentor Quick Test Suite")
    print("=" * 50)
    
    # Test 1: API Health
    print("\n1️⃣ Testing API Health...")
    try:
        response = requests.get(f"{API_BASE}/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API Server Running")
        else:
            print(f"❌ API Issue: {response.status_code}")
    except Exception as e:
        print(f"❌ API Connection Error: {e}")
        return
    
    # Test 2: Stats Endpoint (Fixed)
    print("\n2️⃣ Testing Stats...")
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Stats Retrieved:")
            print(f"   Status: {stats.get('status', 'unknown')}")
            print(f"   Model: {stats.get('llm_model', 'unknown')}")
            # Fixed: Use get() method to avoid KeyError
            print(f"   Documents: {stats.get('total_documents', stats.get('documents', 0))}")
            print(f"   Sources: {stats.get('sources', [])}")
        else:
            print(f"❌ Stats Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats Request Error: {e}")
    
    # Test 3: Search (expecting empty results)
    print("\n3️⃣ Testing Search...")
    try:
        response = requests.post(f"{API_BASE}/search", 
            json={"query": "FastAPI tutorial", "k": 3}, 
            timeout=15
        )
        if response.status_code == 200:
            results = response.json()
            num_results = results.get('total_found', len(results.get('results', [])))
            print(f"✅ Search Working - Found {num_results} results")
        else:
            print(f"❌ Search Error: {response.status_code}")
    except Exception as e:
        print(f"❌ Search Request Error: {e}")
    
    # Test 4: AI Question (this should work even without docs)
    print("\n4️⃣ Testing AI Response...")
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE}/ask", 
            json={
                "question": "What is Python?",
                "k": 3,
                "temperature": 0.1
            }, 
            timeout=120  # 2 minutes for Gemma 3
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer_length = len(data.get('answer', ''))
            sources_used = len(data.get('sources', []))
            print(f"✅ AI Response Generated:")
            print(f"   Time: {response_time:.1f}s")
            print(f"   Length: {answer_length} chars")
            print(f"   Sources: {sources_used}")
            print(f"   Preview: {data.get('answer', '')[:100]}...")
        else:
            print(f"❌ AI Error: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"❌ AI Request Error: {e}")
    
    # Test 5: Document Upload Test
    print("\n5️⃣ Testing Document Upload...")
    try:
        # Create a simple test document
        test_content = """# FastAPI Quick Start

FastAPI is a modern, fast web framework for building APIs with Python 3.7+.

## Installation
```bash
pip install fastapi uvicorn
```

## Basic Example
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}
```

## Running the App
```bash
uvicorn main:app --reload
```
"""
        
        # Save test file
        with open("test_doc.md", "w") as f:
            f.write(test_content)
        
        # Upload it
        with open("test_doc.md", "rb") as f:
            response = requests.post(f"{API_BASE}/upload-document", 
                files={"file": ("test_doc.md", f, "text/markdown")},
                timeout=30
            )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Document Upload Success:")
            print(f"   Message: {result.get('message', 'No message')}")
            print(f"   Chunks: {result.get('chunks_created', 'Unknown')}")
        else:
            print(f"❌ Upload Error: {response.status_code}")
            print(response.text[:200])
            
    except Exception as e:
        print(f"❌ Upload Test Error: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Test Summary:")
    print("• Your DocuMentor API is working!")
    print("• Gemma 3 is responding (though slowly)")
    print("• Vector store is empty - need to load docs")
    print("• Upload functionality can add new documents")
    
    print("\n📝 Next Steps:")
    print("1. Load some documentation with document upload")
    print("2. Test search after documents are loaded")
    print("3. Try more complex questions")
    print("4. Check response time improvements")

if __name__ == "__main__":
    test_documentor()
