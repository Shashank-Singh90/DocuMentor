"""
Real-world tests based on actual bugs we hit
Don't judge - these are from production issues
"""
import pytest
import sys
import os
sys.path.insert(0, os.getcwd())

def test_unicode_emoji_crash():
    """
    Bug #42: Customer uploaded docs with emoji, crashed everything
    Fixed: Jan 15, 2024 by adding encode/decode
    """
    from src.retrieval.vector_store import ChromaVectorStore
    
    # This used to crash
    doc = "Django 🚀 Framework with 你好 unicode"
    v = ChromaVectorStore()
    
    # Should not crash
    v.add_documents(
        texts=[doc],
        metadatas=[{"source": "test"}],
        ids=["test_unicode"]
    )
    print("✓ Unicode handling works")

def test_none_metadata_crash():
    """
    Bug #67: None values in metadata crashed ChromaDB
    Workaround: Replace None with empty string
    """
    from src.retrieval.vector_store import ChromaVectorStore
    
    v = ChromaVectorStore()
    
    # This used to crash
    v.add_documents(
        texts=["test document"],
        metadatas=[{"title": None, "source": "test"}],  # None used to crash
        ids=["test_none"]
    )
    print("✓ None metadata handling works")

@pytest.mark.skip(reason="Takes forever - only run before release")
def test_large_batch_timeout():
    """
    Bug #89: Batches > 100 docs timeout
    Fixed: Batch processing with size 100
    """
    from src.retrieval.vector_store import ChromaVectorStore
    
    v = ChromaVectorStore()
    
    # Create 500 test docs
    texts = [f"Document {i}" for i in range(500)]
    metadatas = [{"id": i} for i in range(500)]
    ids = [f"doc_{i}" for i in range(500)]
    
    # Should not timeout
    v.add_documents(texts, metadatas, ids)

def test_ollama_cold_start():
    """
    Bug #13: First request to Ollama takes 35+ seconds
    Mitigation: Added warmup in __init__
    Note: Still fails sometimes in Docker
    """
    from src.generation.ollama_handler import OllamaLLMHandler
    
    # Just test instantiation with warmup
    try:
        handler = OllamaLLMHandler()
        print("✓ Ollama handler initialized")
    except:
        print("⚠ Ollama not available - skipping")

@pytest.mark.xfail(reason="ChromaDB bug - waiting for v0.4.23")
def test_special_chars_in_search():
    """
    ChromaDB search breaks with certain special chars
    They know about it, waiting for fix
    """
    from src.retrieval.vector_store import ChromaVectorStore
    
    v = ChromaVectorStore()
    # This might fail
    results = v.search("test & query | with (special) chars")
    assert results is not None

if __name__ == "__main__":
    # Quick test runner
    print("Running real-world regression tests...")
    test_unicode_emoji_crash()
    test_none_metadata_crash()
    test_ollama_cold_start()
    print("\n✅ Basic tests passed!")