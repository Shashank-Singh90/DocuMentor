#!/usr/bin/env python3
"""
Setup Script to Fix Critical DocuMentor Issues
This script will:
1. Create missing directory structure
2. Create __init__.py files
3. Update test files to use correct endpoints
"""
import os
from pathlib import Path

def create_directory_structure():
    """Create missing directory structure"""
    print("📁 Creating directory structure...")
    
    directories = [
        "src",
        "src/ingestion",
        "src/retrieval", 
        "src/generation",
        "src/utils",
        "data",
        "data/vectordb",
        "data/scraped",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   ✅ Created/verified: {directory}")

def create_init_files():
    """Create __init__.py files for proper Python package structure"""
    print("\n📦 Creating __init__.py files...")
    
    init_files = [
        "src/__init__.py",
        "src/ingestion/__init__.py",
        "src/retrieval/__init__.py",
        "src/generation/__init__.py", 
        "src/utils/__init__.py"
    ]
    
    for init_file in init_files:
        with open(init_file, 'w') as f:
            f.write('"""DocuMentor package module"""\n')
        print(f"   ✅ Created: {init_file}")

def create_fixed_test_file():
    """Create updated test file with correct endpoints"""
    print("\n🧪 Creating fixed test file...")
    
    test_content = '''#!/usr/bin/env python3
"""
Fixed Test Suite for DocuMentor
Uses correct endpoints and handles all edge cases
"""
import requests
import time
import json
import os

API_BASE = "http://localhost:8000"

def test_all_functionality():
    """Test all DocuMentor functionality with correct endpoints"""
    print("🧪 DocuMentor Fixed Test Suite")
    print("=" * 50)
    
    # Test 1: API Health
    print("\\n1️⃣ Testing API Health...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            print("✅ Health Check Passed")
            print(f"   Status: {health.get('status', 'unknown')}")
            print(f"   Components: {health.get('components', {})}")
        else:
            print(f"❌ Health Check Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Health Check Error: {e}")
    
    # Test 2: Stats
    print("\\n2️⃣ Testing Stats...")
    try:
        response = requests.get(f"{API_BASE}/stats", timeout=10)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Stats Retrieved")
            print(f"   Total Chunks: {stats.get('total_chunks', 0)}")
            print(f"   Sources: {stats.get('total_sources', 0)}")
            print(f"   Status: {stats.get('status', 'unknown')}")
        else:
            print(f"❌ Stats Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Stats Error: {e}")
    
    # Test 3: Search
    print("\\n3️⃣ Testing Search...")
    try:
        response = requests.post(f"{API_BASE}/search", 
            json={"query": "Python basics", "k": 3}, 
            timeout=15
        )
        if response.status_code == 200:
            search_results = response.json()
            print("✅ Search Working")
            print(f"   Results Found: {search_results.get('total_found', 0)}")
            print(f"   Search Time: {search_results.get('search_time', 0):.2f}s")
        else:
            print(f"❌ Search Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Search Error: {e}")
    
    # Test 4: AI Question (with timeout handling)
    print("\\n4️⃣ Testing AI Question...")
    try:
        start_time = time.time()
        response = requests.post(f"{API_BASE}/ask", 
            json={
                "question": "What is Python?",
                "k": 3,
                "temperature": 0.1,
                "max_tokens": 200
            }, 
            timeout=90  # Reasonable timeout
        )
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            ai_response = response.json()
            print("✅ AI Response Generated")
            print(f"   Response Time: {response_time:.1f}s")
            print(f"   Answer Length: {len(ai_response.get('answer', ''))}")
            print(f"   Sources Used: {len(ai_response.get('sources', []))}")
            
            # Show preview
            answer = ai_response.get('answer', '')
            preview = answer[:100] + "..." if len(answer) > 100 else answer
            print(f"   Preview: {preview}")
        else:
            print(f"❌ AI Failed: {response.status_code}")
    except requests.exceptions.Timeout:
        print("❌ AI Response Timed Out (90s)")
    except Exception as e:
        print(f"❌ AI Error: {e}")
    
    # Test 5: Upload (with correct endpoint)
    print("\\n5️⃣ Testing Upload...")
    test_file = "test_upload_fixed.md"
    test_content = """# Test Document

This is a test document to verify the fixed upload functionality.

## Features
- Upload processing
- Document chunking
- Vector storage

## Test Status
This upload test should now work with the fixed DocumentProcessor.
"""
    
    try:
        # Create test file
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        
        # Upload with correct endpoint
        with open(test_file, 'rb') as f:
            files = {'file': (test_file, f, 'text/markdown')}
            response = requests.post(f"{API_BASE}/upload-document", 
                                   files=files, timeout=60)
        
        if response.status_code == 200:
            upload_result = response.json()
            print("✅ Upload Successful")
            print(f"   Chunks Added: {upload_result.get('chunks_added', 0)}")
            print(f"   File Type: {upload_result.get('file_type', 'unknown')}")
            print(f"   Message: {upload_result.get('message', 'N/A')}")
        else:
            print(f"❌ Upload Failed: {response.status_code}")
            if response.text:
                print(f"   Error: {response.text[:200]}")
        
        # Clean up
        os.remove(test_file)
        
    except Exception as e:
        print(f"❌ Upload Error: {e}")
        try:
            os.remove(test_file)
        except:
            pass
    
    # Test 6: Upload Info
    print("\\n6️⃣ Testing Upload Info...")
    try:
        response = requests.get(f"{API_BASE}/upload-info", timeout=10)
        if response.status_code == 200:
            info = response.json()
            print("✅ Upload Info Available")
            formats = info.get('supported_formats', [])
            print(f"   Supported Formats: {[f['extension'] for f in formats]}")
        else:
            print(f"❌ Upload Info Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Upload Info Error: {e}")
    
    print("\\n" + "=" * 50)
    print("🎯 Fixed Test Suite Complete!")
    print("\\nIf all tests pass, your DocuMentor is working correctly!")

if __name__ == "__main__":
    test_all_functionality()
'''
    
    with open('test_fixed_endpoints.py', 'w') as f:
        f.write(test_content)
    
    print("   ✅ Created: test_fixed_endpoints.py")

def create_startup_script():
    """Create a script to easily start the fixed API server"""
    print("\n🚀 Creating startup script...")
    
    startup_content = '''#!/usr/bin/env python3
"""
Start DocuMentor with Fixed API Server
"""
import sys
import os

# Add current directory to path
sys.path.append('.')

try:
    from api_server_fixed import run_server
    print("🚀 Starting DocuMentor with fixed API server...")
    print("📊 Server will be available at: http://localhost:8000")
    print("📖 API docs will be at: http://localhost:8000/docs")
    print("\\nPress Ctrl+C to stop the server")
    
    run_server()
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all files are in the correct location")
except KeyboardInterrupt:
    print("\\n🛑 Server stopped by user")
except Exception as e:
    print(f"❌ Error starting server: {e}")
'''
    
    with open('start_fixed_server.py', 'w') as f:
        f.write(startup_content)
    
    print("   ✅ Created: start_fixed_server.py")

def main():
    """Run all setup fixes"""
    print("🔧 DocuMentor Critical Issues Fix")
    print("=" * 50)
    
    create_directory_structure()
    create_init_files()
    create_fixed_test_file()
    create_startup_script()
    
    print("\n✅ All Fixes Applied!")
    print("\n📋 Next Steps:")
    print("1. Copy the DocumentProcessor code to: src/ingestion/document_processor.py")
    print("2. Copy the fixed API server code to: api_server_fixed.py")
    print("3. Stop your current API server (Ctrl+C)")
    print("4. Start the fixed server: python start_fixed_server.py")
    print("5. Run tests: python test_fixed_endpoints.py")
    
    print("\n🎯 Expected Results After Fixes:")
    print("• Upload functionality should work")
    print("• No more FastAPI deprecation warnings")
    print("• All endpoints should have correct names")
    print("• Tests should pass without 404 errors")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()
