#!/usr/bin/env python3
"""
Diagnose Gemma 3 Performance Issues
Test Ollama/Gemma 3 directly to identify timeout causes
"""
import requests
import json
import time
import sys

OLLAMA_URL = "http://localhost:11434"

def test_ollama_direct():
    """Test Ollama directly without DocuMentor"""
    print("🔧 Diagnosing Gemma 3 Performance Issues")
    print("=" * 50)
    
    # Test 1: Check Ollama status
    print("\n1️⃣ Checking Ollama Status...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            gemma3_found = False
            for model in models:
                if 'gemma3' in model['name']:
                    size_gb = model.get('size', 0) / (1024**3)
                    print(f"✅ Found: {model['name']} ({size_gb:.1f}GB)")
                    gemma3_found = True
            
            if not gemma3_found:
                print("❌ No Gemma 3 model found")
                return False
        else:
            print(f"❌ Ollama not responding: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Ollama: {e}")
        return False
    
    # Test 2: Simple prompt test
    print("\n2️⃣ Testing Simple Prompt...")
    simple_prompt = "What is Python? Give a brief answer."
    
    try:
        start_time = time.time()
        response = requests.post(f"{OLLAMA_URL}/api/generate", 
            json={
                "model": "gemma3:4b",
                "prompt": simple_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 100,  # Limit to 100 tokens
                    "num_ctx": 2048     # Smaller context
                }
            },
            timeout=60
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '').strip()
            print(f"✅ Simple prompt successful ({response_time:.1f}s)")
            print(f"   Answer: {answer[:100]}...")
            
            # Check token stats
            if 'eval_count' in result:
                tokens_generated = result.get('eval_count', 0)
                eval_duration = result.get('eval_duration', 0) / 1e9
                tokens_per_sec = tokens_generated / eval_duration if eval_duration > 0 else 0
                print(f"   Tokens generated: {tokens_generated}")
                print(f"   Speed: {tokens_per_sec:.1f} tokens/sec")
        else:
            print(f"❌ Simple prompt failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Simple prompt timed out (60s)")
        return False
    except Exception as e:
        print(f"❌ Simple prompt error: {e}")
        return False
    
    # Test 3: Complex prompt with context (similar to DocuMentor)
    print("\n3️⃣ Testing Complex Prompt with Context...")
    
    context = """
Django Models Documentation:
Django models are Python classes that define the structure of your database tables. 
Here's how to create models with relationships:

class Author(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    published_date = models.DateField()
"""
    
    complex_prompt = f"""Context:
{context}

Question: How do I create a Django model with foreign keys?

Please provide a clear answer based on the context above."""
    
    try:
        start_time = time.time()
        response = requests.post(f"{OLLAMA_URL}/api/generate", 
            json={
                "model": "gemma3:4b",
                "prompt": complex_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 300,  # Moderate length
                    "num_ctx": 4096,    # Moderate context
                    "stop": ["Human:", "Question:", "Context:"]
                }
            },
            timeout=90
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get('response', '').strip()
            print(f"✅ Complex prompt successful ({response_time:.1f}s)")
            print(f"   Answer length: {len(answer)} chars")
            print(f"   Answer preview: {answer[:150]}...")
            
            # Performance analysis
            if response_time > 60:
                print("⚠️ Response time > 60s - may cause timeouts in DocuMentor")
            elif response_time > 30:
                print("⚠️ Response time > 30s - slower than optimal")
            else:
                print("✅ Good response time for DocuMentor")
                
        else:
            print(f"❌ Complex prompt failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Complex prompt timed out (90s)")
        print("🔧 This explains the DocuMentor timeouts!")
        return False
    except Exception as e:
        print(f"❌ Complex prompt error: {e}")
        return False
    
    # Test 4: Memory/Resource check
    print("\n4️⃣ Checking System Resources...")
    try:
        response = requests.get(f"{OLLAMA_URL}/api/ps", timeout=5)
        if response.status_code == 200:
            running_models = response.json().get('models', [])
            for model in running_models:
                name = model.get('name', 'Unknown')
                size = model.get('size', 0) / (1024**3)
                print(f"   Running: {name} ({size:.1f}GB)")
        
        # Check if multiple models running
        if len(running_models) > 1:
            print("⚠️ Multiple models running - may cause resource contention")
        
    except Exception as e:
        print(f"⚠️ Could not check running models: {e}")
    
    return True

def suggest_optimizations():
    """Suggest performance optimizations"""
    print("\n🚀 Performance Optimization Suggestions")
    print("=" * 50)
    
    print("\n1️⃣ Ollama Configuration:")
    print("   • Reduce context window: OLLAMA_NUM_CTX=4096")
    print("   • Limit response length: OLLAMA_NUM_PREDICT=500")
    print("   • Ensure only one model loaded at a time")
    
    print("\n2️⃣ DocuMentor Configuration (.env):")
    print("   • MODEL_N_CTX=4096 (instead of 8192)")
    print("   • MAX_TOKENS=500 (instead of 2048)")  
    print("   • TEMPERATURE=0.1 (for consistency)")
    
    print("\n3️⃣ System Optimizations:")
    print("   • Close other applications to free RAM")
    print("   • Ensure Gemma 3 is the only model running")
    print("   • Consider using smaller model if available (gemma3:2b)")
    
    print("\n4️⃣ PowerShell Commands to Try:")
    print("   # Stop all models and restart specific one")
    print("   ollama stop gemma3:4b")
    print("   ollama run gemma3:4b")
    
    print("\n   # Check resource usage")
    print("   ollama ps")
    print("   ollama list")

def test_api_integration():
    """Test DocuMentor API with simpler parameters"""
    print("\n🧪 Testing DocuMentor API with Optimized Settings")
    print("=" * 50)
    
    # Simple question that should work quickly
    simple_question = "What is Python?"
    
    try:
        start_time = time.time()
        response = requests.post("http://localhost:8000/ask", 
            json={
                "question": simple_question,
                "k": 3,  # Fewer sources
                "temperature": 0.1,
                "max_tokens": 200  # Shorter response
            },
            timeout=60  # Shorter timeout
        )
        
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '')
            sources = len(data.get('sources', []))
            
            print(f"✅ DocuMentor API successful ({response_time:.1f}s)")
            print(f"   Answer length: {len(answer)} chars")
            print(f"   Sources used: {sources}")
            print(f"   Answer: {answer[:100]}...")
            
            if response_time < 30:
                print("✅ Good performance - API is working!")
            else:
                print("⚠️ Slow but working - consider optimizations")
                
        else:
            print(f"❌ API failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ API still timing out - need Ollama optimization")
    except Exception as e:
        print(f"❌ API error: {e}")

if __name__ == "__main__":
    print("This script will help diagnose Gemma 3 timeout issues...")
    print("Make sure Ollama is running: ollama serve")
    
    input("Press Enter to start diagnostics...")
    
    success = test_ollama_direct()
    
    if success:
        print("\n✅ Ollama/Gemma 3 basic functionality working")
        test_api_integration()
    else:
        print("\n❌ Ollama/Gemma 3 has issues - fix these first")
    
    suggest_optimizations()
    
    print("\n" + "=" * 50)
    print("Next steps:")
    print("1. Apply suggested optimizations")
    print("2. Restart Ollama and DocuMentor")
    print("3. Test with simpler questions first")
    print("4. Gradually increase complexity")
