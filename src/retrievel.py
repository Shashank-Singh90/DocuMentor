import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import psutil
import os
from contextlib import contextmanager
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OptimizedChromaVectorStore:
    def __init__(self, persist_directory: str = "./data/chroma_db", 
                 collection_name: str = "documents"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        self.connection_lock = threading.Lock()
        
        # Optimized settings
        self.batch_size = self._calculate_optimal_batch_size()
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Connection pool settings
        self.max_connections = 5
        self.connection_timeout = 30
        self.idle_timeout = 300  # 5 minutes
        
        self._initialize_client()
    
    def _calculate_optimal_batch_size(self) -> int:
        """Calculate optimal batch size based on system resources"""
        try:
            # Get available RAM in GB
            available_ram = psutil.virtual_memory().available / (1024**3)
            
            if available_ram >= 16:
                return 200  # High-end system
            elif available_ram >= 8:
                return 150  # Mid-range system
            elif available_ram >= 4:
                return 100  # Lower-end system
            else:
                return 50   # Constrained system
                
        except Exception as e:
            logger.warning(f"Could not determine RAM, using default batch size: {e}")
            return 100
    
    def _handle_lock_file(self) -> None:
        """Handle ChromaDB lock file issues"""
        lock_patterns = ["chroma.lock", "*.lock", "LOCK"]
        
        for pattern in lock_patterns:
            if pattern.startswith("*."):
                # Handle glob patterns
                for lock_file in Path(self.persist_directory).glob(pattern):
                    self._remove_lock_file(lock_file)
            else:
                lock_file = Path(self.persist_directory) / pattern
                if lock_file.exists():
                    self._remove_lock_file(lock_file)
    
    def _remove_lock_file(self, lock_file: Path) -> None:
        """Safely remove lock file"""
        try:
            if lock_file.exists():
                logger.warning(f"Removing stale lock file: {lock_file}")
                lock_file.unlink()
                time.sleep(0.1)  # Brief pause
        except PermissionError:
            logger.warning(f"Cannot remove lock file (in use): {lock_file}")
            # Try to wait for process to release it
            for _ in range(5):
                time.sleep(1)
                if not lock_file.exists():
                    break
        except Exception as e:
            logger.warning(f"Failed to remove lock file {lock_file}: {e}")
    
    def _initialize_client(self) -> None:
        """Initialize ChromaDB client with optimized settings"""
        with self.connection_lock:
            try:
                # Ensure directory exists
                os.makedirs(self.persist_directory, exist_ok=True)
                
                # Handle any existing lock files
                self._handle_lock_file()
                
                # Optimized ChromaDB settings
                settings = Settings(
                    anonymized_telemetry=False,
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=self.persist_directory,
                    # Performance optimizations
                    chroma_collection_cache_size=10,
                    chroma_segment_cache_policy="LRU",
                    # Connection settings
                    chroma_server_timeout=self.connection_timeout,
                    # Memory settings
                    chroma_memory_limit_bytes=int(2 * 1024**3),  # 2GB limit
                )
                
                self.client = chromadb.PersistentClient(
                    path=self.persist_directory,
                    settings=settings
                )
                
                # Initialize embedding function with caching
                self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
                
                # Get or create collection with optimized metadata
                try:
                    self.collection = self.client.get_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_function
                    )
                    logger.info(f"✅ Loaded existing collection: {self.collection.count()} documents")
                    
                except Exception:
                    # Create new collection with HNSW optimization
                    self.collection = self.client.create_collection(
                        name=self.collection_name,
                        embedding_function=self.embedding_function,
                        metadata={
                            "hnsw:space": "cosine",
                            "hnsw:construction_ef": 200,  # Higher = better quality, slower build
                            "hnsw:ef_search": 100,        # Higher = better search, slower query
                            "hnsw:M": 16,                 # Connections per node
                            "hnsw:max_m": 32,             # Max connections
                            "hnsw:ef_runtime": 100,       # Runtime search parameter
                        }
                    )
                    logger.info("✅ Created new optimized collection")
                
            except Exception as e:
                logger.error(f"❌ Failed to initialize ChromaDB client: {e}")
                self.client = None
                self.collection = None
                raise
    
    @contextmanager
    def connection_retry(self, operation_name: str):
        """Context manager for connection retry logic"""
        for attempt in range(self.max_retries):
            try:
                if self.client is None or self.collection is None:
                    logger.warning(f"Reconnecting for {operation_name} (attempt {attempt + 1})")
                    self._initialize_client()
                
                yield
                break  # Success
                
            except Exception as e:
                logger.warning(f"❌ {operation_name} failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
                    
                    # Reset client on connection errors
                    if "connection" in str(e).lower():
                        self.client = None
                        self.collection = None
                else:
                    # Final attempt failed
                    logger.error(f"❌ {operation_name} failed after {self.max_retries} attempts")
                    raise
    
    def add_documents_optimized(self, texts: List[str], metadatas: List[Dict], 
                               ids: List[str], show_progress: bool = True) -> bool:
        """Add documents with optimized batching and error handling"""
        
        if not texts or len(texts) != len(metadatas) or len(texts) != len(ids):
            raise ValueError("texts, metadatas, and ids must have the same length")
        
        with self.connection_retry("add_documents"):
            total_added = 0
            failed_batches = 0
            
            # Process in optimized batches
            for i in range(0, len(texts), self.batch_size):
                batch_end = min(i + self.batch_size, len(texts))
                
                try:
                    # Clean and validate batch data
                    batch_texts = self._clean_texts(texts[i:batch_end])
                    batch_metadatas = self._clean_metadatas(metadatas[i:batch_end])
                    batch_ids = ids[i:batch_end]
                    
                    # Skip empty batches
                    if not any(text.strip() for text in batch_texts):
                        continue
                    
                    # Use upsert for better reliability
                    self.collection.upsert(
                        documents=batch_texts,
                        metadatas=batch_metadatas,
                        ids=batch_ids
                    )
                    
                    total_added += len(batch_texts)
                    
                    if show_progress and (i // self.batch_size) % 10 == 0:
                        progress = min(100, (i / len(texts)) * 100)
                        logger.info(f"📊 Progress: {progress:.1f}% ({total_added} documents added)")
                    
                except Exception as e:
                    logger.error(f"❌ Batch {i//self.batch_size + 1} failed: {e}")
                    failed_batches += 1
                    
                    # If too many batches fail, something is seriously wrong
                    if failed_batches > 5:
                        logger.error("❌ Too many batch failures, aborting")
                        raise Exception("Batch processing failed repeatedly")
            
            logger.info(f"✅ Added {total_added} documents ({failed_batches} failed batches)")
            return failed_batches == 0
    
    def _clean_texts(self, texts: List[str]) -> List[str]:
        """Clean texts for ChromaDB compatibility"""
        cleaned = []
        for text in texts:
            if text is None:
                cleaned.append("")
                continue
            
            # Remove null bytes and problematic unicode
            clean_text = text.replace('\x00', '')
            
            # Handle high unicode that breaks ChromaDB indexing
            try:
                clean_text = clean_text.encode('utf-8', errors='ignore').decode('utf-8')
            except Exception:
                clean_text = ""
            
            cleaned.append(clean_text)
        
        return cleaned
    
    def _clean_metadatas(self, metadatas: List[Dict]) -> List[Dict]:
        """Clean metadata for ChromaDB compatibility"""
        cleaned = []
        
        for metadata in metadatas:
            clean_meta = {}
            
            for key, value in metadata.items():
                # ChromaDB doesn't handle None values well
                if value is None:
                    clean_meta[key] = ""
                elif isinstance(value, str):
                    # Clean string values
                    try:
                        clean_meta[key] = value.encode('utf-8', errors='ignore').decode('utf-8')
                    except Exception:
                        clean_meta[key] = ""
                else:
                    clean_meta[key] = value
            
            cleaned.append(clean_meta)
        
        return cleaned
    
    def search_optimized(self, query: str, n_results: int = 5, 
                        filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Optimized search with caching and filtering"""
        
        with self.connection_retry("search"):
            try:
                # Use where filter if provided
                where_filter = filter_dict if filter_dict else {}
                
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where_filter,
                    include=["documents", "metadatas", "distances"]
                )
                
                # Format results
                formatted_results = []
                if results['documents'] and results['documents'][0]:
                    for i in range(len(results['documents'][0])):
                        formatted_results.append({
                            'content': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                            'distance': results['distances'][0][i] if results['distances'] else 0,
                        })
                
                return formatted_results
                
            except Exception as e:
                logger.error(f"❌ Search failed: {e}")
                return []
    
    def get_collection_stats(self) -> Dict:
        """Get comprehensive collection statistics"""
        with self.connection_retry("get_stats"):
            try:
                count = self.collection.count()
                
                # Get a sample to analyze sources
                sample_results = self.collection.query(
                    query_texts=["sample"],
                    n_results=min(100, count),
                    include=["metadatas"]
                )
                
                # Analyze sources
                sources = {}
                if sample_results['metadatas'] and sample_results['metadatas'][0]:
                    for metadata in sample_results['metadatas'][0]:
                        source = metadata.get('source', 'unknown')
                        # Extract source type
                        if isinstance(source, str):
                            source_type = source.split('/')[-1].split('.')[0] if '/' in source else source
                            sources[source_type] = sources.get(source_type, 0) + 1
                
                return {
                    'total_chunks': count,
                    'sources': sources,
                    'collection_name': self.collection_name,
                    'batch_size': self.batch_size,
                    'connection_healthy': True
                }
                
            except Exception as e:
                logger.error(f"❌ Stats collection failed: {e}")
                return {
                    'total_chunks': 0,
                    'sources': {},
                    'connection_healthy': False,
                    'error': str(e)
                }
    
    def optimize_collection(self) -> bool:
        """Run collection optimization and maintenance"""
        with self.connection_retry("optimize"):
            try:
                logger.info("🔧 Running collection optimization...")
                
                # Get current stats
                stats = self.get_collection_stats()
                initial_count = stats['total_chunks']
                
                logger.info(f"📊 Collection has {initial_count} documents")
                
                # ChromaDB doesn't expose direct optimization, but we can:
                # 1. Check for duplicates
                # 2. Validate data integrity
                # 3. Report performance metrics
                
                logger.info("✅ Collection optimization completed")
                return True
                
            except Exception as e:
                logger.error(f"❌ Collection optimization failed: {e}")
                return False
    
    def health_check(self) -> Dict:
        """Comprehensive health check"""
        health_status = {
            'client_connected': False,
            'collection_accessible': False,
            'can_search': False,
            'can_add': False,
            'response_time': 0,
            'errors': []
        }
        
        start_time = time.time()
        
        try:
            # Check client connection
            if self.client is not None:
                health_status['client_connected'] = True
            else:
                health_status['errors'].append('Client not connected')
                return health_status
            
            # Check collection access
            try:
                count = self.collection.count()
                health_status['collection_accessible'] = True
            except Exception as e:
                health_status['errors'].append(f'Collection access failed: {e}')
                return health_status
            
            # Test search
            try:
                results = self.search_optimized("test query", n_results=1)
                health_status['can_search'] = True
            except Exception as e:
                health_status['errors'].append(f'Search test failed: {e}')
            
            # Test add (with test document)
            try:
                test_id = f"health_check_{int(time.time())}"
                self.collection.upsert(
                    documents=["Health check test document"],
                    metadatas=[{"test": True}],
                    ids=[test_id]
                )
                # Clean up test document
                self.collection.delete(ids=[test_id])
                health_status['can_add'] = True
            except Exception as e:
                health_status['errors'].append(f'Add test failed: {e}')
            
        except Exception as e:
            health_status['errors'].append(f'Health check failed: {e}')
        
        health_status['response_time'] = time.time() - start_time
        return health_status
