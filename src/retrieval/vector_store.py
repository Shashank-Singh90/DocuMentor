"""
Vector Store using ChromaDB
Migration history:
- 2023-12: Started with Pinecone (too expensive)
- 2024-01: Moved to Weaviate (complex setup)
- 2024-02: Settled on ChromaDB (good enough)
"""
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import time
from pathlib import Path
from typing import List, Dict, Optional
from src.utils.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)

class ChromaVectorStore:
    def __init__(self):
        self.persist_directory = settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = settings.COLLECTION_NAME
        
        # Chroma lock file issue - happens after crashes
        lock_file = Path(self.persist_directory) / "chroma.lock"
        if lock_file.exists():
            logger.warning("Removing stale lock file...")
            try:
                lock_file.unlink()  # Nuclear option but works
            except:
                pass  # Sometimes Windows locks it
        
        # Initialize client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Get embedding function
        self.embedding_function = embedding_functions.DefaultEmbeddingFunction()
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Loaded collection: {self.collection.count()} docs")
        except:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info("Created new collection")
    
    def add_documents(self, texts: List[str], metadatas: List[dict], ids: List[str]):
        """Add documents - using upsert because add() is flaky
        
        ChromaDB bugs we're working around:
        - None values crash it (replace with "")
        - Unicode > U+10000 breaks indexing
        - Batches > 100 timeout randomly
        """
        BATCH_SIZE = 100  # Found by trial and error
        
        added = 0
        for i in range(0, len(texts), BATCH_SIZE):
            batch_end = min(i + BATCH_SIZE, len(texts))
            
            # Clean metadata - Chroma hates None
            clean_meta = []
            for m in metadatas[i:batch_end]:
                # This is dumb but necessary
                clean = {}
                for k, v in m.items():
                    if v is None:
                        clean[k] = ""
                    elif isinstance(v, str):
                        # Strip high unicode that breaks Chroma
                        clean[k] = v.encode('utf-8', 'ignore').decode('utf-8')
                    else:
                        clean[k] = v
                clean_meta.append(clean)
            
            # Clean texts too
            clean_texts = []
            for t in texts[i:batch_end]:
                # Remove null bytes and high unicode
                cleaned = t.replace('\x00', '').encode('utf-8', 'ignore').decode('utf-8')
                clean_texts.append(cleaned)
            
            # Try to add with retry
            for retry in range(3):  # Magic retry number
                try:
                    self.collection.upsert(
                        documents=clean_texts,
                        metadatas=clean_meta,
                        ids=ids[i:batch_end]
                    )
                    added += len(clean_texts)
                    break
                except Exception as e:
                    if "quota" in str(e).lower():
                        # Hit the undocumented 10K limit
                        logger.error("ChromaDB quota - need cleanup")
                        raise
                    elif retry < 2:
                        # Sometimes works on retry
                        logger.warning(f"Retry {retry + 1} for batch {i//BATCH_SIZE}")
                        time.sleep(0.5 * (retry + 1))  # Backoff
                    else:
                        logger.error(f"Failed batch {i//BATCH_SIZE}: {e}")
                        # Skip this batch rather than fail everything
                        break
            
            # Don't hammer ChromaDB
            if len(texts) > 500:
                time.sleep(0.1)  # Helps with large imports
        
        logger.info(f"Added {added}/{len(texts)} documents")
        return added
    
    def search(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """Search for similar documents
        
        Note: ChromaDB search is weird with short queries
        """
        # Clean query
        query = query.encode('utf-8', 'ignore').decode('utf-8')
        
        # Short queries need padding (discovered through testing)
        if len(query.split()) < 3:
            query = f"{query} documentation reference"  # Hack but improves results
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(k, 100),  # ChromaDB max is 100
                where=filter_dict
            )
            
            # Unpack weird ChromaDB response format
            documents = results.get('documents', [[]])[0]
            metadatas = results.get('metadatas', [[]])[0]
            distances = results.get('distances', [[]])[0]
            
            # Format for API
            formatted = []
            for doc, meta, dist in zip(documents, metadatas, distances):
                formatted.append({
                    'content': doc,
                    'metadata': meta or {},
                    'score': 1 - dist  # Convert distance to similarity
                })
            
            return formatted
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []  # Return empty rather than crash
    
    def get_collection_stats(self) -> Dict:
        """Get collection statistics"""
        try:
            count = self.collection.count()
            # Hacky way to get sources
            sample = self.collection.get(limit=1000)  # Can't get all, too slow
            sources = {}
            for meta in sample.get('metadatas', []):
                if meta and 'source' in meta:
                    src = meta['source']
                    sources[src] = sources.get(src, 0) + 1
            
            return {
                'total_chunks': count,
                'sources': sources,
                'sample_size': len(sample.get('ids', []))
            }
        except:
            return {'total_chunks': 0, 'sources': {}}

# Keep old import name for backwards compat
VectorStore = ChromaVectorStore
