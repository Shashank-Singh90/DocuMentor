import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import numpy as np
from typing import List, Dict, Optional, Tuple
import json
from pathlib import Path
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class ChromaVectorStore:
    def __init__(
        self,
        persist_directory: str = None,
        collection_name: str = None,
        embedding_model: str = None
    ):
        """Initialize ChromaDB vector store"""
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.COLLECTION_NAME
        self.embedding_model = embedding_model or settings.EMBEDDING_MODEL
        
        logger.info(f"🗄️ Initializing ChromaDB at {self.persist_directory}")
        
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
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model
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
            logger.info(f"📚 Loaded existing collection: {self.collection_name}")
            
            # Check collection stats
            count = collection.count()
            logger.info(f"📊 Collection contains {count} documents")
            
        except Exception as e:
            logger.info(f"🆕 Creating new collection: {self.collection_name}")
            collection = self.client.create_collection(
                name=self.collection_name,
                embedding_function=self.embedding_function,
                metadata={
                    "hnsw:space": "cosine",
                    "description": "DocuMentor knowledge base"
                }
            )
            logger.info(f"✅ Created new collection: {self.collection_name}")
            
        return collection
    
    def add_chunks_from_file(self, embedded_chunks_file: str = "embedded_chunks.json"):
        """Load embedded chunks from file and add to vector store"""
        chunks_path = settings.PROCESSED_DATA_DIR / embedded_chunks_file
        
        if not chunks_path.exists():
            logger.error(f"❌ Embedded chunks file not found: {chunks_path}")
            logger.info("💡 Run the embedding engine first: python -m src.chunking.embeddings")
            return
            
        logger.info(f"📚 Loading embedded chunks from {chunks_path}")
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            embedded_chunks = json.load(f)
            
        logger.info(f"📄 Loaded {len(embedded_chunks)} embedded chunks")
        self.add_chunks(embedded_chunks)
        
    def add_chunks(self, chunks: List[Dict]):
        """Add chunks to vector store"""
        if not chunks:
            logger.warning("⚠️ No chunks to add!")
            return
            
        logger.info(f"📥 Adding {len(chunks)} chunks to vector store...")
        
        # Prepare data for ChromaDB
        ids = []
        documents = []
        metadatas = []
        embeddings = []
        
        for chunk in chunks:
            chunk_id = chunk['metadata']['chunk_id']
            content = chunk['content']
            metadata = chunk['metadata'].copy()
            embedding = chunk.get('embedding', [])
            
            # Clean metadata (ChromaDB doesn't like nested objects)
            clean_metadata = self._clean_metadata(metadata)
            
            ids.append(chunk_id)
            documents.append(content)
            metadatas.append(clean_metadata)
            embeddings.append(embedding)
            
        try:
            # Add to collection in batches to avoid memory issues
            batch_size = 100
            total_added = 0
            
            for i in range(0, len(ids), batch_size):
                batch_ids = ids[i:i + batch_size]
                batch_docs = documents[i:i + batch_size]
                batch_metadata = metadatas[i:i + batch_size]
                batch_embeddings = embeddings[i:i + batch_size]
                
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_docs,
                    metadatas=batch_metadata,
                    embeddings=batch_embeddings
                )
                
                total_added += len(batch_ids)
                logger.info(f"📥 Added batch {i//batch_size + 1}: {total_added}/{len(chunks)} chunks")
                
            logger.info(f"✅ Successfully added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"❌ Error adding chunks to vector store: {e}")
            raise
            
    def _clean_metadata(self, metadata: Dict) -> Dict:
        """Clean metadata for ChromaDB compatibility"""
        clean_metadata = {}
        
        for key, value in metadata.items():
            # Convert all values to strings or numbers (ChromaDB requirement)
            if isinstance(value, (str, int, float, bool)):
                clean_metadata[key] = value
            elif isinstance(value, list):
                # Convert list to string
                clean_metadata[key] = str(value)
            else:
                # Convert other types to string
                clean_metadata[key] = str(value)
                
        return clean_metadata
        
    def search(
        self,
        query: str,
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """Search for similar chunks using text query"""
        logger.info(f"🔍 Searching for: '{query}' (top {k} results)")
        
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
                    'score': 1 - results['distances'][0][i]  # Convert distance to similarity
                })
                
            logger.info(f"✅ Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Error searching vector store: {e}")
            return []
        
    def search_with_embedding(
        self,
        query_embedding: List[float],
        k: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> List[Dict]:
        """Search using pre-computed embedding"""
        logger.info(f"🔍 Searching with embedding vector (top {k} results)")
        
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
                    'score': 1 - results['distances'][0][i]
                })
                
            logger.info(f"✅ Found {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"❌ Error searching with embedding: {e}")
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
                logger.warning(f"⚠️ Document {document_id} not found")
                return []
                
            # Use the document content to find similar ones
            document_text = doc_results['documents'][0]
            
            # Search for similar documents (excluding the original)
            results = self.search(document_text, k=k+1)
            
            # Filter out the original document
            filtered_results = [r for r in results if r['id'] != document_id][:k]
            
            return filtered_results
            
        except Exception as e:
            logger.error(f"❌ Error finding similar documents: {e}")
            return []
    
    def delete_collection(self):
        """Delete the entire collection"""
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info(f"🗑️ Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Error deleting collection: {e}")
            
    def reset_collection(self):
        """Reset collection (delete and recreate)"""
        logger.info(f"🔄 Resetting collection: {self.collection_name}")
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
                        source_counts = {}
                        
                        for metadata in all_docs['metadatas']:
                            source = metadata.get('source', 'unknown')
                            source_counts[source] = source_counts.get(source, 0) + 1
                            
                        stats['sources'] = source_counts
                    except Exception:
                        # If too many documents, skip detailed stats
                        pass
                        
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting collection stats: {e}")
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
    logger.info(f"📊 Collection stats: {stats}")
    
    # Test searches
    test_queries = [
        "How to create a FastAPI application?",
        "What is LangChain?",
        "Authentication in web APIs",
        "Building chatbots with AI"
    ]
    
    for query in test_queries:
        logger.info(f"🔍 Testing search: '{query}'")
        results = vector_store.search(query, k=3)
        
        logger.info(f"📋 Top {len(results)} results:")
        for i, result in enumerate(results):
            score = result.get('score', 0)
            source = result.get('metadata', {}).get('source', 'Unknown')
            title = result.get('metadata', {}).get('title', 'Unknown')
            logger.info(f"   {i+1}. [{source}] {title} (score: {score:.3f})")
        logger.info("")
    
    logger.info("✅ Vector store test completed!")

if __name__ == "__main__":
    test_vector_store()