#!/usr/bin/env python3
"""
Comprehensive test suite for the RAG System
Tests all core functionality and system integration
"""

import sys
import requests
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test if all system components can be imported"""
    print("Testing system imports...")
    try:
        from rag_system.core import DocumentChunker, VectorStore
        from rag_system.core.generation.llm_handler import llm_service
        from rag_system.core.processing import document_processor
        from rag_system.core.search import web_search_provider
        from rag_system.config import get_settings
        from rag_system.web.app import main as web_main
        print("[PASS] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("Testing configuration...")
    try:
        from rag_system.config import get_settings
        settings = get_settings()
        print(f"[PASS] Configuration loaded")
        print(f"   ChromaDB path: {settings.chroma_persist_directory}")
        print(f"   Collection: {settings.collection_name}")
        return True
    except Exception as e:
        print(f"[FAIL] Configuration test failed: {e}")
        return False

def test_vector_store():
    """Test vector store functionality"""
    print("Testing vector store...")
    try:
        from rag_system.core import VectorStore
        vector_store = VectorStore()
        stats = vector_store.get_collection_stats()
        print(f"[PASS] Vector store initialized")
        print(f"   Document count: {stats.get('total_chunks', 0)}")
        print(f"   Sources: {len(stats.get('sources', {}))}")
        results = vector_store.search("Python programming", k=3)
        print(f"   Search test: {len(results)} results found")
        return True
    except Exception as e:
        print(f"[FAIL] Vector store test failed: {e}")
        return False

def test_document_processing():
    """Test document processing"""
    print("Testing document processor...")
    try:
        from rag_system.core.processing import document_processor
        formats = document_processor.get_supported_formats()
        print(f"[PASS] Document processor initialized")
        print(f"   Supported formats: {len(formats)}")
        test_content = "This is a test document for the RAG system."
        result = document_processor.process_file("test.txt", test_content.encode('utf-8'))
        status = "[PASS]" if result['success'] else "[FAIL]"
        print(f"   Text processing: {status}")
        return result['success']
    except Exception as e:
        print(f"[FAIL] Document processor test failed: {e}")
        return False

def test_llm_providers():
    """Test LLM providers"""
    print("Testing LLM providers...")
    try:
        from rag_system.core.generation.llm_handler import llm_service
        provider_status = llm_service.get_provider_status()
        available_providers = llm_service.get_available_providers()
        print(f"[PASS] LLM handler initialized")
        print(f"   Available providers: {len(available_providers)}")
        for provider, available in provider_status.items():
            status = "[PASS]" if available else "[FAIL]"
            print(f"   {provider}: {status}")
        return len(available_providers) > 0
    except Exception as e:
        print(f"[FAIL] LLM provider test failed: {e}")
        return False

def test_api_server():
    """Test API server connection"""
    print("Testing API server...")
    api_url = "http://127.0.0.1:8100"
    try:
        response = requests.get(f"{api_url}/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"[PASS] API server responding")
            print(f"   Version: {data.get('version', 'Unknown')}")
            return True
        else:
            print(f"[FAIL] API returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"[INFO] API server not available")
        print(f"   Start with: python api_server.py")
        return False

def test_performance():
    """Test system performance"""
    print("Testing system performance...")
    try:
        from rag_system.core import VectorStore
        vector_store = VectorStore()
        start_time = time.time()
        results = vector_store.search("machine learning", k=5)
        search_time = time.time() - start_time
        print(f"[PASS] Performance test completed")
        print(f"   Search time: {search_time:.3f}s")
        print(f"   Results returned: {len(results)}")
        return search_time < 3.0  # Should be under 3 seconds
    except Exception as e:
        print(f"[FAIL] Performance test failed: {e}")
        return False

def main():
    """Run comprehensive test suite"""
    print("DocuMentor Comprehensive Test Suite")
    print("=" * 50)

    # Define all tests
    tests = [
        ("System Imports", test_imports),
        ("Configuration", test_configuration),
        ("Vector Store", test_vector_store),
        ("Document Processing", test_document_processing),
        ("LLM Providers", test_llm_providers),
        ("API Server", test_api_server),
        ("Performance", test_performance)
    ]

    # Run tests
    results = {}
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 30)
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"[FAIL] {test_name} failed with exception: {e}")
            results[test_name] = False

    # Results summary
    print("\n" + "=" * 50)
    print("TEST RESULTS SUMMARY")
    print("=" * 50)

    passed = 0
    total = len(tests)

    for test_name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{test_name:<20} | {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

    # Recommendations
    if passed == total:
        print("All tests passed! System is ready for production.")
    elif passed >= total * 0.8:
        print("Most tests passed. Minor issues detected.")
    else:
        print("Multiple issues detected. Please review failed tests.")

    print("\nTo start the system:")
    print("   Web UI: python main.py")
    print("   API Server: python api_server.py")
    print("   Complete System: python launcher.py")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)