import sys
import os
import json
import asyncio
from pathlib import Path

# Add src to path
sys.path.append('src')

from chunking.smart_chunker import SmartDocumentChunker
from retrieval.vector_store import ChromaVectorStore
from utils.logger import get_logger

async def main():
    logger = get_logger(__name__)
    logger.info("🚀 Processing new documentation...")
    
    # Files to process
    files = [
        "data/scraped/django_docs.json",
        "data/scraped/react_nextjs_docs.json", 
        "data/scraped/python_docs.json"
    ]
    
    chunker = SmartDocumentChunker()
    vector_store = ChromaVectorStore()
    
    total_added = 0
    
    for file_path in files:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                # Skip validation for now - all our docs are clean
                docs = json.load(f)
            
            logger.info(f"📖 Processing {len(docs)} documents from {file_path}")
            
            for doc in docs:
                chunks = await chunker.chunk_document(
                    content=doc['content'],
                    metadata={
                        'title': doc['title'],
                        'source': doc['source'],
                        'url': doc['url'],
                        'doc_type': doc.get('doc_type', 'general')
                    }
                )
                
                if chunks:
                    texts = [c['content'] for c in chunks]
                    metadatas = [c['metadata'] for c in chunks]
                    ids = [f"{doc['source']}_{hash(c['content'])}" for c in chunks]
                    
                    vector_store.add_documents(texts, metadatas, ids)
                    total_added += len(chunks)
            
            logger.info(f"✅ Processed {file_path}")
    
    logger.info(f"🎉 Added {total_added} new chunks total!")
    
    # Get stats
    stats = vector_store.get_collection_stats()
    logger.info(f"📊 Total chunks now: {stats.get('total_chunks', 0)}")

if __name__ == "__main__":
    asyncio.run(main())




