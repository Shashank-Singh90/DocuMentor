"""
Test Gemma 3 Integration with DocuMentor
Run this to verify everything is working correctly
"""
import sys
import os
sys.path.append('.')

from src.generation.ollama_handler import OllamaLLMHandler
from src.retrieval.vector_store import ChromaVectorStore
from src.utils.logger import get_logger
import time

logger = get_logger(__name__)

def test_llama4_integration():
    """Complete integration test for Gemma 3"""
    print("🧪 Testing Gemma 3 Integration with DocuMentor")
    print("=" * 50)
    
    # Step 1: Check Ollama and Model
    print("\n1️⃣ Checking Ollama Connection...")
    try:
        handler = OllamaLLMHandler(model_name="gemma3:4b")
        status = handler.check_model_status()
        
        if status['status'] == 'available':
            print(f"✅ Gemma 3 Model Found: {status['model']}")
            print(f"   Size: {status['size'] / (1024**3):.1f} GB")
            print(f"   Family: {status.get('family', 'Gemma 3')}")
        else:
            print(f"❌ Model Status: {status}")
            return False
            
    except Exception as e:
        print(f"❌ Error connecting to Ollama: {e}")
        return False
    
    # Step 2: Test Vector Store
    print("\n2️⃣ Testing Vector Store...")
    try:
        vector_store = ChromaVectorStore()
        stats = vector_store.get_stats()
        print(f"✅ Vector Store Active")
        print(f"   Total documents: {stats.get('total_documents', 0)}")
        print(f"   Collections: {stats.get('collections', [])}")
    except Exception as e:
        print(f"❌ Vector Store Error: {e}")
        return False
    
    # Step 3: Test Question Answering
    print("\n3️⃣ Testing Question Answering with Gemma 3...")
    test_question = "What is FastAPI and how do I create a simple API endpoint?"
    
    try:
        # Search for relevant docs
        print(f"   Searching for: '{test_question}'")
        search_results = vector_store.search(test_question, k=3)
        
        if search_results:
            print(f"   Found {len(search_results)} relevant documents")
            
            # Generate answer with Gemma 3
            print("   Generating answer with Gemma 3...")
            start_time = time.time()
            
            answer = handler.generate_answer(
                question=test_question,
                search_results=search_results,
                max_tokens=512,
                temperature=0.1
            )
            
            response_time = time.time() - start_time
            
            print(f"\n✅ Answer generated in {response_time:.2f} seconds:")
            print("-" * 50)
            print(answer[:500] + "..." if len(answer) > 500 else answer)
            print("-" * 50)
            
        else:
            print("⚠️  No search results found - vector store might be empty")
            
    except Exception as e:
        print(f"❌ Question Answering Error: {e}")
        return False
    
    # Step 4: Test API Server
    print("\n4️⃣ Testing API Server...")
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Server is running")
        else:
            print("⚠️  API Server not responding - start with: python api_server.py")
    except:
        print("⚠️  API Server not running - start with: python api_server.py")
    
    print("\n" + "=" * 50)
    print("🎉 Gemma 3 Integration Test Complete!")
    return True

if __name__ == "__main__":
    test_llama4_integration()
