import json
from pathlib import Path
import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

from src.retrieval.vector_store import ChromaVectorStore
from src.utils.logger import get_logger

def simple_chunk_text(text, chunk_size=1000, overlap=200):
    """Simple text chunking"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence end in the last 100 chars
            last_part = text[max(0, end-100):end]
            sentence_end = last_part.rfind('. ')
            if sentence_end > 0:
                end = end - 100 + sentence_end + 1
        
        chunk = text[start:end].strip()
        if chunk and len(chunk) > 50:  # Only keep meaningful chunks
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def main():
    logger = get_logger(__name__)
    logger.info("🚀 Adding new documentation to DocuMentor...")
    
    try:
        # Initialize vector store
        vector_store = ChromaVectorStore()
        
        # Get initial stats
        initial_stats = vector_store.get_collection_stats()
        initial_count = initial_stats.get('total_chunks', 0)
        logger.info(f"📊 Initial chunks in database: {initial_count}")
        
        # Files to process
        files = [
            ("data/scraped/django_docs.json", "django"),
            ("data/scraped/react_nextjs_docs.json", "react"), 
            ("data/scraped/python_docs.json", "python"),
            ("data/scraped/docker_docs.json", "docker"),
            ("data/scraped/database_docs.json", "database"),
            ("data/scraped/typescript_docs.json", "typescript")
        ]
        
        total_new_chunks = 0
        
        for file_path, source_prefix in files:
            if not Path(file_path).exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                continue
            
            logger.info(f"📖 Processing {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                
                logger.info(f"📄 Loaded {len(documents)} documents")
                
                # Process each document
                chunks_added_for_source = 0
                
                for i, doc in enumerate(documents):
                    try:
                        # Get document content
                        content = doc.get('content', '')
                        if len(content) < 100:  # Skip very short documents
                            continue
                        
                        # Simple chunking
                        chunks = simple_chunk_text(content, chunk_size=800, overlap=150)
                        
                        # Add each chunk individually using the add method
                        for j, chunk_text in enumerate(chunks):
                            try:
                                # Create metadata
                                metadata = {
                                    'title': doc.get('title', 'Unknown'),
                                    'source': doc.get('source', source_prefix),
                                    'url': doc.get('url', ''),
                                    'doc_type': doc.get('doc_type', 'general'),
                                    'chunk_index': j,
                                    'total_chunks': len(chunks)
                                }
                                
                                # Create unique ID
                                doc_id = f"{source_prefix}_{i}_{j}_{hash(chunk_text) % 10000}"
                                
                                # Add to vector store (try different method names)
                                if hasattr(vector_store, 'add'):
                                    vector_store.add(
                                        text=chunk_text,
                                        metadata=metadata,
                                        doc_id=doc_id
                                    )
                                elif hasattr(vector_store, 'add_document'):
                                    vector_store.add_document(
                                        text=chunk_text,
                                        metadata=metadata,
                                        doc_id=doc_id
                                    )
                                elif hasattr(vector_store, 'add_texts'):
                                    vector_store.add_texts(
                                        texts=[chunk_text],
                                        metadatas=[metadata],
                                        ids=[doc_id]
                                    )
                                else:
                                    # Try to use the collection directly
                                    vector_store.collection.add(
                                        documents=[chunk_text],
                                        metadatas=[metadata],
                                        ids=[doc_id]
                                    )
                                
                                chunks_added_for_source += 1
                                total_new_chunks += 1
                                
                            except Exception as e:
                                logger.warning(f"⚠️ Error adding chunk {j} from doc {i}: {e}")
                                continue
                        
                        # Progress update
                        if (i + 1) % 5 == 0:
                            logger.info(f"📋 Processed {i + 1}/{len(documents)} documents, added {chunks_added_for_source} chunks so far")
                            
                    except Exception as e:
                        logger.error(f"❌ Error processing document {i}: {e}")
                        continue
                
                logger.info(f"✅ Completed {file_path} - Added {chunks_added_for_source} chunks")
                
            except Exception as e:
                logger.error(f"❌ Error processing file {file_path}: {e}")
                continue
        
        # Get final stats
        final_stats = vector_store.get_collection_stats()
        final_count = final_stats.get('total_chunks', 0)
        
        logger.info("🎉 Documentation addition completed!")
        logger.info(f"📊 Chunks added: {total_new_chunks}")
        logger.info(f"📊 Total chunks now: {final_count}")
        logger.info(f"📊 Sources in database: {len(final_stats.get('sources', {}))}")
        
        # Show source breakdown
        logger.info("📋 Updated source breakdown:")
        for source, count in final_stats.get('sources', {}).items():
            logger.info(f"  • {source.upper()}: {count} chunks")
        
        logger.info("🚀 Refresh your DocuMentor and try asking about Django, React, or Python!")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()