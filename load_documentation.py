#!/usr/bin/env python3
"""
Load Documentation into DocuMentor Vector Store
This script loads the scraped documentation files into ChromaDB
"""
import sys
import os
import json
import time
from pathlib import Path

# Add project root to path
sys.path.append('.')

try:
    from src.retrieval.vector_store import ChromaVectorStore
    from src.utils.logger import get_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

logger = get_logger(__name__)

def load_documentation_data():
    """Load all scraped documentation into the vector store"""
    
    print("🚀 Loading Documentation into DocuMentor")
    print("=" * 50)
    
    # Initialize vector store
    try:
        vector_store = ChromaVectorStore()
        print("✅ Vector store initialized")
    except Exception as e:
        print(f"❌ Failed to initialize vector store: {e}")
        return False
    
    # Find all scraped data files
    data_dir = Path("data/scraped")
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    json_files = list(data_dir.glob("*.json"))
    if not json_files:
        print(f"❌ No JSON files found in {data_dir}")
        return False
    
    print(f"📁 Found {len(json_files)} documentation files:")
    for file in json_files:
        print(f"   - {file.name}")
    
    total_docs_added = 0
    
    # Process each documentation file
    # Quick and dirty for hackathon - needs proper error recovery
    for file_path in json_files:
        print(f"\n📖 Processing {file_path.name}...")
        
        try:
            # Load the JSON data
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, dict):
                if 'documents' in data:
                    documents = data['documents']
                else:
                    # Single document
                    documents = [data]
            elif isinstance(data, list):
                documents = data
            else:
                print(f"⚠️ Unexpected data structure in {file_path.name}")
                continue
            
            print(f"   📄 Found {len(documents)} documents")
            
            # Process documents
            docs_from_this_file = 0
            source_name = file_path.stem.replace('_docs', '').replace('_', ' ').title()
            
            for i, doc in enumerate(documents):
                try:
                    # Extract content and metadata
                    if isinstance(doc, dict):
                        content = doc.get('content', str(doc))
                        title = doc.get('title', f"Document {i+1}")
                        url = doc.get('url', '')
                        doc_type = doc.get('doc_type', source_name.lower())
                    else:
                        # If it's just a string
                        content = str(doc)
                        title = f"{source_name} Document {i+1}"
                        url = ''
                        doc_type = source_name.lower()
                    
                    # Skip empty content
                    if not content or len(content.strip()) < 50:
                        continue
                    
                    # Create chunks (simple approach - split by paragraphs)
                    chunks = []
                    paragraphs = content.split('\n\n')
                    
                    current_chunk = ""
                    for para in paragraphs:
                        para = para.strip()
                        if not para:
                            continue
                            
                        # If adding this paragraph would make chunk too long, save current chunk
                        if len(current_chunk) + len(para) > 1000 and current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = para
                        else:
                            current_chunk += "\n\n" + para if current_chunk else para
                    
                    # Add final chunk
                    if current_chunk.strip():
                        chunks.append(current_chunk.strip())
                    
                    # Add chunks to vector store
                    for j, chunk_text in enumerate(chunks):
                        if len(chunk_text.strip()) < 30:  # Skip very small chunks
                            continue
                            
                        try:
                            # Create metadata
                            metadata = {
                                'source': source_name,
                                'title': title,
                                'url': url,
                                'doc_type': doc_type,
                                'chunk_index': j,
                                'file_source': file_path.name
                            }
                            
                            # Create unique ID
                            doc_id = f"{source_name}_{i}_{j}_{hash(chunk_text) % 10000}"
                            
                            # Add to vector store using the collection directly
                            vector_store.collection.add(
                                documents=[chunk_text],
                                metadatas=[metadata],
                                ids=[doc_id]
                            )
                            
                            docs_from_this_file += 1
                            
                        except Exception as e:
                            print(f"   ⚠️ Error adding chunk {j} from doc {i}: {e}")
                            continue
                    
                    # Progress update
                    if (i + 1) % 10 == 0:
                        print(f"   📋 Processed {i + 1}/{len(documents)} documents...")
                
                except Exception as e:
                    print(f"   ⚠️ Error processing document {i}: {e}")
                    continue
            
            print(f"   ✅ Added {docs_from_this_file} chunks from {file_path.name}")
            total_docs_added += docs_from_this_file
            
        except Exception as e:
            print(f"   ❌ Error processing {file_path.name}: {e}")
            continue
    
    print(f"\n🎉 Documentation loading complete!")
    print(f"📊 Total chunks added: {total_docs_added}")
    
    # Test the loaded data
    print(f"\n🔍 Testing loaded data...")
    try:
        # Get collection info
        count = vector_store.collection.count()
        print(f"   📈 Vector store now contains: {count} documents")
        
        # Test search
        test_results = vector_store.search("FastAPI tutorial", k=3)
        print(f"   🔍 Test search returned: {len(test_results)} results")
        
        if test_results:
            print("   📋 Sample results:")
            for i, result in enumerate(test_results[:2]):
                metadata = result.get('metadata', {})
                source = metadata.get('source', 'Unknown')
                title = metadata.get('title', 'Unknown')[:50]
                print(f"      {i+1}. [{source}] {title}...")
        
    except Exception as e:
        print(f"   ⚠️ Error testing loaded data: {e}")
    
    print(f"\n✅ DocuMentor is now ready with {total_docs_added} documentation chunks!")
    return True

if __name__ == "__main__":
    success = load_documentation_data()
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Test search: python quick_test.py")
        print("2. Ask questions via API: http://localhost:8000/docs")
        print("3. Try complex queries about the loaded documentation")
    else:
        print("\n❌ Loading failed. Check the errors above and try again.")
    
    print("\n" + "=" * 50)
