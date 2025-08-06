import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
from pathlib import Path
from typing import List, Dict
from src.chunking.smart_chunker import SmartDocumentChunker
from src.retrieval.vector_store import ChromaVectorStore
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def process_and_add_documentation():
    """Process scraped documentation and add to vector store"""
    
    logger.info("🚀 Starting documentation processing and ingestion...")
    
    try:
        # Initialize components
        chunker = SmartDocumentChunker()
        vector_store = ChromaVectorStore()
        
        # Files to process
        scraped_files = [
            ("data/scraped/django_docs.json", "Django"),
            ("data/scraped/react_nextjs_docs.json", "React/Next.js"), 
            ("data/scraped/python_docs.json", "Python")
        ]
        
        total_chunks_added = 0
        
        for file_path, doc_type in scraped_files:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                continue
                
            logger.info(f"📖 Processing {doc_type} documentation from {file_path}")
            
            # Load scraped documents
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                documents = json.load(f)
            
            logger.info(f"📄 Loaded {len(documents)} {doc_type} documents")
            
            # Process each document
            chunks_for_this_source = []
            
            for i, doc in enumerate(documents):
                try:
                    # Chunk the document
                    chunks = await chunker.chunk_document(
                        content=doc['content'],
                        metadata={
                            'title': doc['title'],
                            'source': doc['source'],
                            'url': doc['url'],
                            'doc_type': doc.get('doc_type', 'general'),
                            'scraped_at': doc.get('scraped_at', '')
                        }
                    )
                    
                    chunks_for_this_source.extend(chunks)
                    
                    if (i + 1) % 5 == 0:
                        logger.info(f"📋 Processed {i + 1}/{len(documents)} {doc_type} documents")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing document {doc.get('title', 'Unknown')}: {e}")
                    continue
            
            # Add chunks to vector store
            if chunks_for_this_source:
                logger.info(f"💾 Adding {len(chunks_for_this_source)} {doc_type} chunks to vector store...")
                
                try:
                    # Prepare documents for vector store
                    texts = [chunk['content'] for chunk in chunks_for_this_source]
                    metadatas = [chunk['metadata'] for chunk in chunks_for_this_source]
                    ids = [f"{chunk['metadata']['source']}_{i}_{hash(chunk['content'])}" for i, chunk in enumerate(chunks_for_this_source)]
                    
                    # Add to vector store in batches
                    batch_size = 50
                    for i in range(0, len(texts), batch_size):
                        batch_texts = texts[i:i+batch_size]
                        batch_metadatas = metadatas[i:i+batch_size]
                        batch_ids = ids[i:i+batch_size]
                        
                        vector_store.add_documents(
                            texts=batch_texts,
                            metadatas=batch_metadatas,
                            ids=batch_ids
                        )
                        
                        logger.info(f"✅ Added batch {i//batch_size + 1} ({len(batch_texts)} chunks)")
                    
                    total_chunks_added += len(chunks_for_this_source)
                    logger.info(f"✅ Added {len(chunks_for_this_source)} {doc_type} chunks successfully")
                
                except Exception as e:
                    logger.error(f"❌ Error adding {doc_type} chunks to vector store: {e}")
                    continue
            
            else:
                logger.warning(f"⚠️ No chunks generated for {doc_type}")
        
        # Get updated statistics
        try:
            stats = vector_store.get_collection_stats()
            
            logger.info("🎉 Documentation processing completed!")
            logger.info(f"📊 Total new chunks added: {total_chunks_added}")
            logger.info(f"📊 Total chunks in database: {stats.get('total_chunks', 0)}")
            logger.info(f"📊 Sources in database: {len(stats.get('sources', {}))}")
            
            # Show source breakdown
            logger.info("📋 Updated source breakdown:")
            for source, count in stats.get('sources', {}).items():
                logger.info(f"  • {source.upper()}: {count} chunks")
                
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            
    except Exception as e:
        logger.error(f"❌ Fatal error in processing: {e}")
        raise

def main():
    """Main function"""
    try:
        asyncio.run(process_and_add_documentation())
        logger.info("🎉 All done! Your DocuMentor now has expanded knowledge!")
        logger.info("🚀 Refresh your browser and try asking about Django, React, or Python!")
    except Exception as e:
        logger.error(f"❌ Script failed: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()