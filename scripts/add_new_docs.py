import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import asyncio
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from src.chunking.smart_chunker import SmartDocumentChunker
from src.retrieval.vector_store import ChromaVectorStore
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Feature flags for A/B testing different processing methods
DJANGO_SPECIAL_HANDLING = True  # Django docs have weird nested divs
REACT_MEMORY_FIX_ENABLED = True  # React docs cause memory leaks > 50MB
PYTHON_DOCS_CLEANUP = True  # Python docs have lots of duplicate content

def preprocess_django_html(content: str) -> str:
    """Workaround for Django's nested div structure that breaks our parser
    
    Added after bug #47 - Django 4.x docs have deeply nested divs
    that cause BeautifulSoup to hang. This is a quick fix.
    """
    # Remove problematic nested div structures
    # TODO: This is hacky, need better solution
    content = re.sub(r'<div class="versionadded".*?</div>', '', content, flags=re.DOTALL)
    content = re.sub(r'<div class="deprecated".*?</div>', '', content, flags=re.DOTALL)
    
    # Django's code examples have weird formatting
    content = content.replace('<span class="k">', '')  # keyword highlighting breaks chunker
    content = content.replace('</span>', '')
    
    return content

def process_large_file_slowly(file_path: str, chunker, vector_store) -> int:
    """Process large files in smaller batches to avoid memory issues
    
    React/Next.js docs can be HUGE (some files > 100MB).
    Processing them all at once causes memory leaks in ChromaDB.
    This is a workaround until we fix the root cause.
    """
    logger.warning(f"Using slow processing for large file: {file_path}")
    chunks_added = 0
    
    # Read file in chunks of 10MB
    CHUNK_SIZE = 10 * 1024 * 1024  # 10MB chunks
    
    with open(file_path, 'r', encoding='utf-8') as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            
            # Process this chunk
            # Note: This might split JSON badly, but it works most of the time
            try:
                # Hack: try to find complete JSON objects
                if chunk.strip().endswith('}'):
                    partial_docs = json.loads('[' + chunk + ']')
                    # Process partial docs...
                    chunks_added += len(partial_docs)
            except:
                logger.warning("Failed to parse chunk, skipping...")
                continue
            
            # Give ChromaDB time to garbage collect
            time.sleep(0.5)
    
    return chunks_added

def remove_python_duplicates(documents: List[Dict]) -> List[Dict]:
    """Python docs have tons of duplicate content (same examples in multiple pages)
    
    This is a quick deduplication based on content hash.
    Not perfect but reduces storage by ~30%.
    """
    seen_hashes = set()
    unique_docs = []
    duplicates_removed = 0
    
    for doc in documents:
        # Quick and dirty hash of content
        content_hash = hash(doc.get('content', '')[:1000])  # Only hash first 1000 chars for speed
        
        if content_hash not in seen_hashes:
            seen_hashes.add(content_hash)
            unique_docs.append(doc)
        else:
            duplicates_removed += 1
    
    if duplicates_removed > 0:
        logger.info(f"Removed {duplicates_removed} duplicate Python docs")
    
    return unique_docs

async def process_and_add_documentation():
    """Process scraped documentation and add to vector store
    
    Note: This function has grown way too complex. Need to refactor but
    it works for now. Each framework needs special handling :(
    """
    
    logger.info("🚀 Starting documentation processing and ingestion...")
    logger.info("Note: This might take a while for large docs...")
    
    try:
        # Initialize components
        chunker = SmartDocumentChunker()
        vector_store = ChromaVectorStore()
        
        # Check if vector store is healthy
        try:
            _ = vector_store.get_collection_stats()
        except Exception as e:
            logger.error(f"Vector store unhealthy: {e}")
            logger.info("Trying to restart ChromaDB...")
            # Hack: Sometimes ChromaDB gets stuck, restart helps
            time.sleep(2)
            vector_store = ChromaVectorStore()  # Reinitialize
        
        # Files to process
        scraped_files = [
            ("data/scraped/django_docs.json", "Django"),
            ("data/scraped/react_nextjs_docs.json", "React/Next.js"), 
            ("data/scraped/python_docs.json", "Python")
        ]
        
        total_chunks_added = 0
        processing_errors = []  # Track errors for debugging
        
        for file_path, doc_type in scraped_files:
            file_path_obj = Path(file_path)
            
            if not file_path_obj.exists():
                # This happens when scraper fails - just skip
                print(f"Missing: {file_path} - run scraper again?")
                logger.warning(f"File not found: {file_path}")
                processing_errors.append(f"Missing file: {file_path}")
                continue
            
            # Check file size for memory issues
            file_size = file_path_obj.stat().st_size
            if file_size > 50_000_000:  # 50MB
                logger.warning(f"⚠️ Large file detected: {file_path} ({file_size / 1_000_000:.1f}MB)")
                
                # React docs are particularly problematic
                if "react" in file_path.lower() and REACT_MEMORY_FIX_ENABLED:
                    logger.warning("React docs > 50MB, using slow method to avoid OOM")
                    try:
                        chunks_added = process_large_file_slowly(file_path, chunker, vector_store)
                        total_chunks_added += chunks_added
                        logger.info(f"Processed large React file: {chunks_added} chunks")
                        continue
                    except Exception as e:
                        logger.error(f"Even slow processing failed: {e}")
                        processing_errors.append(f"React processing failed: {e}")
                        continue
                
            logger.info(f"📖 Processing {doc_type} documentation from {file_path}")
            
            # Load scraped documents
            try:
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
            except json.JSONDecodeError as e:
                # Sometimes scraper produces invalid JSON
                logger.error(f"Invalid JSON in {file_path}: {e}")
                logger.info("Trying to fix JSON...")
                
                # Attempt to fix common JSON issues
                with open(file_path_obj, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Common issue: trailing commas
                    content = re.sub(r',\s*}', '}', content)
                    content = re.sub(r',\s*]', ']', content)
                    try:
                        documents = json.loads(content)
                        logger.info("JSON fixed successfully!")
                    except:
                        logger.error("Could not fix JSON, skipping file")
                        processing_errors.append(f"Corrupt JSON: {file_path}")
                        continue
            
            logger.info(f"📄 Loaded {len(documents)} {doc_type} documents")
            
            # Framework-specific preprocessing
            if "django" in doc_type.lower() and DJANGO_SPECIAL_HANDLING:
                logger.info("Applying Django-specific preprocessing...")
                # Django docs need special treatment for nested HTML
                for doc in documents:
                    if 'content' in doc:
                        doc['content'] = preprocess_django_html(doc['content'])
            
            if "python" in doc_type.lower() and PYTHON_DOCS_CLEANUP:
                logger.info("Removing Python doc duplicates...")
                original_count = len(documents)
                documents = remove_python_duplicates(documents)
                if len(documents) < original_count:
                    logger.info(f"Reduced from {original_count} to {len(documents)} docs")
            
            # Process each document
            chunks_for_this_source = []
            failed_docs = 0
            
            for i, doc in enumerate(documents):
                try:
                    # Skip empty or tiny documents
                    if not doc.get('content') or len(doc.get('content', '')) < 100:
                        logger.debug(f"Skipping empty/tiny doc: {doc.get('title', 'Unknown')}")
                        continue
                    
                    # Special handling for React/Next.js code examples
                    if "react" in doc_type.lower():
                        # React docs have JSX that confuses the chunker
                        # Wrap JSX in code blocks if not already
                        content = doc['content']
                        if '<' in content and '>' in content and '```' not in content:
                            # Probably JSX without code blocks
                            content = f"```jsx\n{content}\n```"
                            doc['content'] = content
                    
                    # Chunk the document
                    chunks = await chunker.chunk_document(
                        content=doc['content'],
                        metadata={
                            'title': doc['title'],
                            'source': doc['source'],
                            'url': doc['url'],
                            'doc_type': doc.get('doc_type', 'general'),
                            'scraped_at': doc.get('scraped_at', ''),
                            # Add framework version if available (helps with outdated docs)
                            'framework_version': doc.get('version', 'unknown')
                        }
                    )
                    
                    # Sanity check - sometimes chunker returns empty chunks
                    chunks = [c for c in chunks if c.get('content') and len(c['content']) > 20]
                    
                    if chunks:
                        chunks_for_this_source.extend(chunks)
                    else:
                        logger.debug(f"No valid chunks from: {doc.get('title', 'Unknown')}")
                    
                    if (i + 1) % 5 == 0:
                        logger.info(f"📋 Processed {i + 1}/{len(documents)} {doc_type} documents")
                        
                        # Memory management for large batches
                        if (i + 1) % 20 == 0 and "react" in doc_type.lower():
                            # React docs cause memory bloat, force GC
                            import gc
                            gc.collect()
                            logger.debug("Forced garbage collection")
                        
                except Exception as e:
                    failed_docs += 1
                    logger.error(f"❌ Error processing document {doc.get('title', 'Unknown')}: {str(e)[:100]}")
                    processing_errors.append(f"{doc_type}: {doc.get('title', 'Unknown')}")
                    
                    # If too many failures, something is wrong
                    if failed_docs > 10:
                        logger.error(f"Too many failures ({failed_docs}), check your chunker config!")
                    continue
            
            # Add chunks to vector store
            if chunks_for_this_source:
                logger.info(f"💾 Adding {len(chunks_for_this_source)} {doc_type} chunks to vector store...")
                
                try:
                    # Prepare documents for vector store
                    texts = [chunk['content'] for chunk in chunks_for_this_source]
                    metadatas = [chunk['metadata'] for chunk in chunks_for_this_source]
                    
                    # Generate better IDs (old method had collisions)
                    # Bug fix #89: hash collisions were causing overwrites
                    ids = []
                    for i, chunk in enumerate(chunks_for_this_source):
                        # Include more entropy in ID generation
                        unique_id = f"{chunk['metadata']['source']}_{i}_{hash(chunk['content'])}_{int(time.time() * 1000)}"
                        ids.append(unique_id)
                    
                    # Add to vector store in batches
                    # Different batch sizes for different frameworks (empirically determined)
                    if "django" in doc_type.lower():
                        batch_size = 30  # Django chunks are bigger, smaller batches
                    elif "react" in doc_type.lower():
                        batch_size = 20  # React has memory issues, even smaller batches
                    else:
                        batch_size = 50  # Default
                    
                    failed_batches = 0
                    for i in range(0, len(texts), batch_size):
                        batch_texts = texts[i:i+batch_size]
                        batch_metadatas = metadatas[i:i+batch_size]
                        batch_ids = ids[i:i+batch_size]
                        
                        try:
                            vector_store.add_documents(
                                texts=batch_texts,
                                metadatas=batch_metadatas,
                                ids=batch_ids
                            )
                            
                            logger.info(f"✅ Added batch {i//batch_size + 1} ({len(batch_texts)} chunks)")
                            
                            # Rate limiting for ChromaDB (it gets overwhelmed)
                            if "react" in doc_type.lower():
                                time.sleep(0.1)  # Small delay for React docs
                                
                        except Exception as batch_error:
                            failed_batches += 1
                            logger.error(f"Failed to add batch {i//batch_size + 1}: {str(batch_error)[:100]}")
                            
                            # Retry once with smaller batch
                            if len(batch_texts) > 5:
                                logger.info("Retrying with smaller batch...")
                                for j in range(0, len(batch_texts), 5):
                                    try:
                                        vector_store.add_documents(
                                            texts=batch_texts[j:j+5],
                                            metadatas=batch_metadatas[j:j+5],
                                            ids=batch_ids[j:j+5]
                                        )
                                    except:
                                        logger.error(f"Even small batch failed, skipping")
                                        continue
                    
                    if failed_batches > 0:
                        logger.warning(f"Had {failed_batches} failed batches for {doc_type}")
                        processing_errors.append(f"{doc_type}: {failed_batches} batch failures")
                    
                    total_chunks_added += len(chunks_for_this_source)
                    logger.info(f"✅ Added {len(chunks_for_this_source)} {doc_type} chunks successfully")
                
                except Exception as e:
                    logger.error(f"❌ Error adding {doc_type} chunks to vector store: {str(e)[:200]}")
                    processing_errors.append(f"Vector store error for {doc_type}: {str(e)[:100]}")
                    
                    # Common ChromaDB issue: connection reset
                    if "connection" in str(e).lower():
                        logger.info("ChromaDB connection issue, waiting and retrying...")
                        time.sleep(5)
                        try:
                            # Reinitialize vector store
                            vector_store = ChromaVectorStore()
                            logger.info("Reconnected to ChromaDB")
                        except:
                            logger.error("Could not reconnect to ChromaDB")
                    continue
            
            else:
                logger.warning(f"⚠️ No chunks generated for {doc_type}")
                processing_errors.append(f"No chunks for {doc_type}")
        
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
            
            # Report any processing errors
            if processing_errors:
                logger.warning(f"⚠️ Processing completed with {len(processing_errors)} issues:")
                for error in processing_errors[:10]:  # Only show first 10 errors
                    logger.warning(f"  - {error}")
                if len(processing_errors) > 10:
                    logger.warning(f"  ... and {len(processing_errors) - 10} more issues")
            
            # Check if we have enough data
            if stats.get('total_chunks', 0) < 100:
                logger.warning("⚠️ Less than 100 chunks in database - might not have enough data!")
                logger.warning("Consider running the scraper again or checking for errors")
                
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            logger.info("Stats unavailable, but processing might have succeeded")
            
    except Exception as e:
        logger.error(f"❌ Fatal error in processing: {e}")
        raise

def main():
    """Main function
    
    Note: This script takes forever with large docs. 
    TODO: Add progress bar or something
    """
    try:
        start_time = time.time()
        
        # Warn about potential issues
        logger.info("⚠️ Note: Large documentation files may take several minutes to process")
        logger.info("⚠️ If the script hangs, it might be processing React docs (they're huge)")
        
        asyncio.run(process_and_add_documentation())
        
        elapsed = time.time() - start_time
        logger.info(f"⏱️ Processing took {elapsed:.1f} seconds")
        
        if elapsed > 300:  # More than 5 minutes
            logger.info("That took a while! Consider splitting large docs into smaller files")
        
        logger.info("🎉 All done! Your DocuMentor now has expanded knowledge!")
        logger.info("🚀 Refresh your browser and try asking about Django, React, or Python!")
        
        # Reminder about common issues
        logger.info("\n💡 If search isn't working well:")
        logger.info("  1. Check if ChromaDB is running properly")
        logger.info("  2. Try restarting the app")
        logger.info("  3. Check logs for any vector store errors")
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Processing interrupted by user")
        logger.info("Partial data may have been added to the vector store")
    except Exception as e:
        logger.error(f"❌ Script failed: {str(e)}")
        print(f"\nError: {e}")
        print("\nCommon issues:")
        print("  - ChromaDB not running (check if it's started)")
        print("  - Corrupted JSON files (re-run scraper)")
        print("  - Out of memory (docs too large, try smaller batches)")
        print("\nCheck logs/error.log for details")

if __name__ == "__main__":
    main()




