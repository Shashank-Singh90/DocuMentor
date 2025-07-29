from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict, Optional
import torch
from tqdm import tqdm
import json
import time
from pathlib import Path
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class EmbeddingEngine:
    def __init__(
        self,
        model_name: str = None,
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """Initialize embedding engine"""
        self.model_name = model_name or settings.EMBEDDING_MODEL
        
        # Detect device
        if device is None:
            if torch.cuda.is_available():
                device = "cuda"
                logger.info("🔥 CUDA available! Using GPU for embeddings")
            else:
                device = "cpu"
                logger.info("💻 Using CPU for embeddings")
        else:
            logger.info(f"🎯 Using specified device: {device}")
            
        self.device = device
        self.batch_size = batch_size
        
        logger.info(f"🧠 Loading embedding model: {self.model_name}")
        start_time = time.time()
        
        try:
            self.model = SentenceTransformer(self.model_name, device=device)
            load_time = time.time() - start_time
            logger.info(f"✅ Model loaded in {load_time:.2f}s")
        except Exception as e:
            logger.error(f"❌ Failed to load model {self.model_name}: {e}")
            logger.info("🔄 Falling back to default model...")
            self.model = SentenceTransformer("all-MiniLM-L6-v2", device=device)
        
        # Get embedding dimension
        self.embedding_dim = self.model.get_sentence_embedding_dimension()
        logger.info(f"📐 Embedding dimension: {self.embedding_dim}")
        
    def embed_chunks_from_file(self, chunks_file: str = "chunks.json") -> List[Dict]:
        """Load chunks from file and embed them"""
        chunks_path = settings.PROCESSED_DATA_DIR / chunks_file
        
        if not chunks_path.exists():
            logger.error(f"❌ Chunks file not found: {chunks_path}")
            logger.info("💡 Run the chunker first: python -m src.chunking.chunker")
            return []
            
        logger.info(f"📚 Loading chunks from {chunks_path}")
        
        with open(chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
            
        logger.info(f"📄 Loaded {len(chunks)} chunks")
        
        return self.embed_chunks(chunks)
        
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Embed a list of chunks"""
        if not chunks:
            logger.warning("⚠️ No chunks to embed!")
            return []
            
        logger.info(f"🚀 Starting embedding generation for {len(chunks)} chunks...")
        
        # Extract texts for embedding
        texts = []
        valid_chunks = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.get('content', '').strip()
            if content:
                texts.append(content)
                valid_chunks.append(chunk)
            else:
                logger.warning(f"⚠️ Empty chunk at index {i}, skipping")
        
        logger.info(f"📝 Processing {len(texts)} valid chunks")
        
        if not texts:
            logger.error("❌ No valid content found in chunks!")
            return []
        
        # Generate embeddings in batches with progress bar
        embeddings = []
        start_time = time.time()
        
        logger.info(f"🔥 Generating embeddings (batch_size={self.batch_size})...")
        
        for i in tqdm(range(0, len(texts), self.batch_size), desc="Embedding batches"):
            batch_texts = texts[i:i + self.batch_size]
            
            try:
                batch_embeddings = self.model.encode(
                    batch_texts,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                    normalize_embeddings=True  # Normalize for better similarity search
                )
                embeddings.extend(batch_embeddings)
                
            except Exception as e:
                logger.error(f"❌ Error embedding batch {i//self.batch_size + 1}: {e}")
                # Add zero vectors for failed batch
                batch_size = len(batch_texts)
                zero_embeddings = np.zeros((batch_size, self.embedding_dim))
                embeddings.extend(zero_embeddings)
        
        embedding_time = time.time() - start_time
        logger.info(f"✅ Embedding generation completed in {embedding_time:.2f}s")
        logger.info(f"⚡ Speed: {len(texts)/embedding_time:.1f} chunks/second")
        
        # Add embeddings to chunks
        embedded_chunks = []
        for chunk, embedding in zip(valid_chunks, embeddings):
            chunk_copy = chunk.copy()
            chunk_copy['embedding'] = embedding.tolist()
            chunk_copy['metadata']['embedding_model'] = self.model_name
            chunk_copy['metadata']['embedding_dim'] = self.embedding_dim
            embedded_chunks.append(chunk_copy)
        
        logger.info(f"✅ Successfully embedded {len(embedded_chunks)} chunks")
        return embedded_chunks
        
    def embed_query(self, query: str) -> np.ndarray:
        """Embed a single query for search"""
        if not query.strip():
            logger.warning("⚠️ Empty query provided")
            return np.zeros(self.embedding_dim)
            
        try:
            embedding = self.model.encode(
                query, 
                convert_to_numpy=True,
                normalize_embeddings=True
            )
            return embedding
        except Exception as e:
            logger.error(f"❌ Error embedding query: {e}")
            return np.zeros(self.embedding_dim)
        
    def save_embeddings(self, chunks: List[Dict], filename: str = "embedded_chunks.json"):
        """Save chunks with embeddings"""
        output_path = settings.PROCESSED_DATA_DIR / filename
        
        logger.info(f"💾 Saving {len(chunks)} embedded chunks...")
        
        # Convert numpy arrays to lists for JSON serialization
        serializable_chunks = []
        embedding_stats = {
            'total_chunks': len(chunks),
            'embedding_dim': self.embedding_dim,
            'model_name': self.model_name,
            'device_used': self.device
        }
        
        for chunk in chunks:
            chunk_copy = chunk.copy()
            if isinstance(chunk_copy.get('embedding'), np.ndarray):
                chunk_copy['embedding'] = chunk_copy['embedding'].tolist()
            serializable_chunks.append(chunk_copy)
            
        # Save chunks
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_chunks, f, indent=2, ensure_ascii=False)
            
        # Save statistics
        stats_path = settings.PROCESSED_DATA_DIR / f"embedding_stats.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump(embedding_stats, f, indent=2)
            
        logger.info(f"✅ Saved embedded chunks to {output_path}")
        logger.info(f"📊 Saved embedding stats to {stats_path}")
        
        return output_path
    
    def calculate_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """Calculate cosine similarity between two embeddings"""
        try:
            # Ensure embeddings are normalized
            embedding1 = embedding1 / np.linalg.norm(embedding1)
            embedding2 = embedding2 / np.linalg.norm(embedding2)
            
            # Calculate cosine similarity
            similarity = np.dot(embedding1, embedding2)
            return float(similarity)
        except Exception as e:
            logger.error(f"❌ Error calculating similarity: {e}")
            return 0.0
    
    def find_similar_chunks(
        self, 
        query_embedding: np.ndarray, 
        embedded_chunks: List[Dict], 
        top_k: int = 5
    ) -> List[Dict]:
        """Find most similar chunks to a query embedding"""
        if not embedded_chunks:
            return []
            
        similarities = []
        
        for i, chunk in enumerate(embedded_chunks):
            chunk_embedding = np.array(chunk.get('embedding', []))
            if chunk_embedding.size > 0:
                similarity = self.calculate_similarity(query_embedding, chunk_embedding)
                similarities.append((similarity, i, chunk))
            
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top k results
        results = []
        for similarity, idx, chunk in similarities[:top_k]:
            result = chunk.copy()
            result['similarity_score'] = similarity
            results.append(result)
            
        return results
    
    def test_embeddings(self, embedded_chunks: List[Dict]):
        """Test the embedding system with sample queries"""
        logger.info("🧪 Testing embedding system...")
        
        test_queries = [
            "How to create a FastAPI application?",
            "What is LangChain?",
            "Authentication in FastAPI",
            "LangChain agents tutorial"
        ]
        
        for query in test_queries:
            logger.info(f"🔍 Testing query: '{query}'")
            
            query_embedding = self.embed_query(query)
            similar_chunks = self.find_similar_chunks(query_embedding, embedded_chunks, top_k=3)
            
            logger.info(f"📋 Top {len(similar_chunks)} similar chunks:")
            for i, chunk in enumerate(similar_chunks):
                score = chunk.get('similarity_score', 0)
                title = chunk.get('metadata', {}).get('title', 'Unknown')
                source = chunk.get('metadata', {}).get('source', 'Unknown')
                logger.info(f"   {i+1}. [{source}] {title} (score: {score:.3f})")
            
            logger.info("")

# Test function
def test_embedding_engine():
    """Test the embedding engine with existing chunks"""
    logger.info("🧪 Testing EmbeddingEngine...")
    
    engine = EmbeddingEngine()
    embedded_chunks = engine.embed_chunks_from_file()
    
    if embedded_chunks:
        output_file = engine.save_embeddings(embedded_chunks)
        logger.info(f"✅ Embedding test completed! Output: {output_file}")
        
        # Run similarity tests
        engine.test_embeddings(embedded_chunks)
        
    else:
        logger.error("❌ No embedded chunks created!")

if __name__ == "__main__":
    test_embedding_engine()