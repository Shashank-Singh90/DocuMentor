# Migration history:
# 2023-12: Started with Pinecone (too expensive)
# 2024-01: Moved to Weaviate (complex setup)
# 2024-02: Settled on ChromaDB (good enough)

try:
    import chromadb  # type: ignore[import]
    from chromadb.config import Settings  # type: ignore[import]
    from chromadb.utils import embedding_functions  # type: ignore[import]
except Exception:  # pragma: no cover - for linting environments without deps
    chromadb = None  # type: ignore[assignment]
    Settings = object  # type: ignore[assignment]
    embedding_functions = None  # type: ignore[assignment]
from typing import List, Dict, Optional
import json
import time
from pathlib import Path
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)


class ChromaVectorStore:
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
        embedding_model: Optional[str] = None
    ):
        """Initialize ChromaDB vector store"""
        self.persist_directory = (
            persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        )
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL

        logger.info("🗄️ Initializing ChromaDB at %s", self.persist_directory)

        # Ensure directory exists
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                persist_directory=self.persist_directory,
                is_persistent=True
            )
        )
        
        # Create embedding function for queries (ChromaDB handles this)
        self.embedding_function = (
            embedding_functions.DefaultEmbeddingFunction()
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            collection = self.client.get_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(
                "📚 Loaded existing collection: %s",
                self.collection_name,
            )
            
            # Check collection stats
            count = collection.count()
            logger.info("📊 Collection contains %s documents", count)
            
        except Exception:
            logger.info("🆕 Creating new collection: %s", self.collection_name)
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "hnsw:space": "cosine",
                    "description": "DocuMentor knowledge base"
                }
            )
            logger.info("✅ Created new collection: %s", self.collection_name)
            
        return collection
    
    def add_chunks_from_file(
        self, embedded_chunks_file: str = "embedded_chunks.json"
    ):
        """Load embedded chunks from file and add to vector store"""
        # Not worth optimizing - only called once at startup
        chunks_path = settings.PROCESSED_DATA_DIR / embedded_chunks_file
        
        if not chunks_path.exists():
            logger.error("❌ Embedded chunks file not found: %s", chunks_path)
            logger.info(
                "💡 Run the embedding engine first: "
                "python -m src.chunking.embeddings"
            )
            return
            
        logger.info("📚 Loading embedded chunks from %s", chunks_path)
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            embedded_chunks = json.load(f)
            
        logger.info("📄 Loaded %s embedded chunks", len(embedded_chunks))
        self.add_chunks(embedded_chunks)
        
    def add_documents(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Add documents to vector store
        
        Note: ChromaDB's add() method was flaky, using upsert instead - Sarah 2024-01
        """
        if not texts:
            logger.warning("⚠️ No documents to add!")
            return
            
        logger.info("📥 Adding %s documents to vector store...", len(texts))
        
        try:
            # Batch size of 100 after testing (50 too slow, 500 causes timeouts)
            BATCH_SIZE = 100
            
            for i in range(0, len(texts), BATCH_SIZE):
                batch_end = min(i + BATCH_SIZE, len(texts))
                
                # ChromaDB doesn't like None values, replace with empty string
                clean_metadata = [{k: v or "" for k, v in m.items()} 
                                for m in metadatas[i:batch_end]]
                
                self.collection.upsert(
                    documents=texts[i:batch_end],
                    metadatas=clean_metadata,
                    ids=ids[i:batch_end]
                )
                
                logger.info(
                    "📥 Added batch %s: %s/%s documents",
                    (i // BATCH_SIZE) + 1,
                    batch_end,
                    len(texts),
                )
                
                # Added sleep after random failures on large batches
                if len(texts) > 500:
                    time.sleep(0.1)  # Hacky but works
                    
        except Exception as e:
            # Specific error we keep hitting
            if "quota" in str(e).lower():
                logger.error(f"Hit ChromaDB quota limit - need to cleanup old docs")
            elif "unicode" in str(e).lower() or "codec" in str(e).lower():
                logger.error(f"ChromaDB error (probably that unicode bug again): {e}")
            else:
                logger.error(f"ChromaDB error during upsert: {e}")
            raise
    
    def add_chunks(self, chunks: List[Dict]):
        """Add chunks to vector store
        
        Note: ChromaDB's add() method was flaky, using upsert instead - Sarah 2024-01
        """
        if not chunks:
            logger.warning("⚠️ No chunks to add!")
            return
            
        logger.info("📥 Adding %s chunks to vector store...", len(chunks))
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for chunk in chunks:
            chunk_id = chunk['metadata']['chunk_id']
            content = chunk['content']
            metadata = chunk['metadata'].copy()
            embedding = chunk.get('embedding') or []
            
            # ChromaDB doesn't like None values, replace with empty string
            clean_document = self._sanitize_doc_text(content)
            clean_metadata = self._sanitize_document_metadata(metadata)
            
            # Sanitize embeddings (replace None with 0.0, fallback to [])
            if isinstance(embedding, list):
                embedding = [0.0 if e is None else e for e in embedding]
            else:
                embedding = []
            
            ids.append(chunk_id)
            documents.append(clean_document)
            metadatas.append(clean_metadata)
            embeddings.append(embedding)
            
        try:
            # Batch size of 100 after testing (50 too slow, 500 causes timeouts)
            BATCH_SIZE = 100
            total_added = 0
            
            for i in range(0, len(ids), BATCH_SIZE):
                batch_end = min(i + BATCH_SIZE, len(ids))
                batch_ids = ids[i:batch_end]
                batch_docs = documents[i:batch_end]
                batch_metadata = metadatas[i:batch_end]
                batch_embeddings = embeddings[i:batch_end]
                
                # Using upsert instead of add - more reliable with duplicates
                self.collection.upsert(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metadata,
                    embeddings=batch_embeddings
                )
                
                total_added += len(batch_ids)
                logger.info(
                    "📥 Added batch %s: %s/%s chunks",
                    (i // BATCH_SIZE) + 1,
                    total_added,
                    len(chunks),
                )
                
                # Added sleep after random failures on large batches
                if len(chunks) > 500:
                    import time
                    time.sleep(0.1)  # Hacky but works
                
            logger.info(
                "✅ Successfully added %s chunks to vector store", len(chunks)
            )
            
        except Exception as e:
            # Specific error we keep hitting
            if "quota" in str(e).lower():
                logger.error(f"Hit ChromaDB quota limit - need to cleanup old docs")
            elif "unicode" in str(e).lower() or "codec" in str(e).lower():
                logger.error(f"ChromaDB error (probably that unicode bug again): {e}")
            else:
                logger.error(f"ChromaDB error during upsert: {e}")
            raise
            
    def _sanitize_document_metadata(self, metadata: Dict) -> Dict:
        """Prepare metadata for ChromaDB compatibility.
        
        ChromaDB doesn't like None values, replace with empty string
        """
        clean_metadata: Dict[str, object] = {}
        for key, value in metadata.items():
            # ChromaDB doesn't like None values, replace with empty string
            if value is None:
                clean_metadata[key] = ""
                continue
            # Convert all values to strings or numbers (ChromaDB requirement)
            if isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif isinstance(value, list):
                clean_metadata[key] = str(value)
            else:
                clean_metadata[key] = str(value)
        return clean_metadata

    def _sanitize_doc_text(self, doc: Optional[str]) -> str:
        """Ensure document text is a safe string (minor naming inconsistency intended)."""
        if doc is None:
            return ""
        return doc
        
    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar chunks using text query"""
        logger.info("🔍 Searching for: '%s' (top %s results)", query, k)
        
        # Build where clause for filtering
        where_clause = filter_dict if filter_dict else None
        
        try:
            # Perform search
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i],
                })
                
            logger.info("✅ Found %s results", len(formatted_results))
            return formatted_results
            
        except Exception as e:
            logger.error("❌ Error searching vector store: %s", e)
            return []
        
    def search_with_embedding(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """Search using pre-computed embedding"""
        logger.info(
            "🔍 Searching with embedding vector (top %s results)",
            k,
        )
        
        where_clause = filter_dict if filter_dict else None
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                where=where_clause,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = []
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    'id': results['ids'][0][i],
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'score': 1 - results['distances'][0][i],
                })
                
            logger.info("✅ Found %s results", len(formatted_results))
            return formatted_results
            
        except Exception as e:
            logger.error("❌ Error searching with embedding: %s", e)
            return []
    
    def get_similar_documents(
        self,
        document_id: str,
        k: int = 5
    ) -> List[Dict]:
        """Find documents similar to a specific document"""
        try:
            # Get the document first
            doc_results = self.collection.get(
                ids=[document_id],
                include=['documents', 'metadatas']
            )
            
            if not doc_results['ids']:
                logger.warning("⚠️ Document %s not found", document_id)
                return []
                
            # Use the document content to find similar ones
            document_text = doc_results['documents'][0]
            
            # Search for similar documents (excluding the original)
            results = self.search(document_text, k=k + 1)
            
            # Filter out the original document
            filtered_results = [r for r in results if r['id'] != document_id][:k]
            
            return filtered_results
            
        except Exception as e:
            logger.error("❌ Error finding similar documents: %s", e)
            return []
    
    def delete_collection(self):
        """Delete the entire collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info("🗑️ Deleted collection: %s", self.collection_name)
        except Exception as e:
            logger.error("❌ Error deleting collection: %s", e)
            
    def reset_collection(self):
        """Reset collection (delete and recreate)"""
        logger.info("🔄 Resetting collection: %s", self.collection_name)
        self.delete_collection()
        self.collection = self._get_or_create_collection()
        
    def get_collection_stats(self) -> Dict:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            
            # Get sample metadata to understand structure
            sample = self.collection.peek(limit=1)
            
            stats = {
                'total_chunks': count,
                'collection_name': self.collection_name,
                'persist_directory': self.persist_directory,
                'embedding_model': self.embedding_model
            }
            
            if sample['metadatas']:
                # Analyze metadata structure
                metadata_keys = list(sample['metadatas'][0].keys())
                stats['metadata_fields'] = metadata_keys
                
                # Count by source if available
                if count > 0:
                    try:
                        # Get all documents to count sources
                        all_docs = self.collection.get(include=['metadatas'])
                        source_counts: Dict[str, int] = {}
                        
                        for metadata in all_docs['metadatas']:
                            source = metadata.get('source', 'unknown')
                            source_counts[source] = source_counts.get(source, 0) + 1
                            
                        stats['sources'] = source_counts
                    except Exception:
                        # If too many documents, skip detailed stats
                        pass
                        
            return stats
            
        except Exception as e:
            logger.error("❌ Error getting collection stats: %s", e)
            return {'error': str(e)}

# Test function
def test_vector_store():
    """Test the vector store with embedded chunks"""
    logger.info("🧪 Testing ChromaVectorStore...")
    
    # Initialize vector store
    vector_store = ChromaVectorStore()
    
    # Reset collection for fresh test
    vector_store.reset_collection()
    
    # Add chunks from file
    vector_store.add_chunks_from_file()
    
    # Get stats
    stats = vector_store.get_collection_stats()
    logger.info("📊 Collection stats: %s", stats)
    
    # Test searches
    test_queries = [
        "How to create a FastAPI application?",
        "What is LangChain?",
        "Authentication in web APIs",
        "Building chatbots with AI"
    ]
    
    for query in test_queries:
        logger.info("🔍 Testing search: '%s'", query)
        results = vector_store.search(query, k=3)
        
        logger.info("📋 Top %s results:", len(results))
        for i, result in enumerate(results):
            score = result.get('score', 0)
            source = result.get('metadata', {}).get('source', 'Unknown')
            title = result.get('metadata', {}).get('title', 'Unknown')
            logger.info(
                "   %s. [%s] %s (score: %.3f)",
                i + 1,
                source,
                title,
                score,
            )
        logger.info("")
    
    logger.info("✅ Vector store test completed!")

if __name__ == "__main__":
    test_vector_store()
