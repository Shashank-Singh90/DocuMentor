"""
Embedding Cache for DocuMentor
Caches embeddings to avoid recomputation and improve performance
"""
import hashlib
import json
import pickle
import time
from typing import List, Optional, Dict, Any
from pathlib import Path
import numpy as np
from rag_system.core.utils.logger import get_logger

logger = get_logger(__name__)

class EmbeddingCache:
    """Cache for text embeddings to improve performance"""

    def __init__(self, cache_dir: str = "./data/embeddings_cache", max_cache_size: int = 10000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size

        self.cache_file = self.cache_dir / "embeddings.pkl"
        self.metadata_file = self.cache_dir / "embedding_metadata.json"

        # Load existing cache
        self.cache = self._load_cache()
        self.metadata = self._load_metadata()

        logger.info(f"Embedding cache initialized with {len(self.cache)} entries")

    def _load_cache(self) -> Dict:
        """Load embedding cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    cache = pickle.load(f)
                    logger.debug(f"Loaded {len(cache)} cached embeddings")
                    return cache
        except Exception as e:
            logger.warning(f"Failed to load embedding cache: {e}")
        return {}

    def _load_metadata(self) -> Dict:
        """Load cache metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load embedding metadata: {e}")
        return {"access_times": {}, "creation_times": {}, "text_lengths": {}}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            # Save embeddings
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)

            # Save metadata
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)

            logger.debug(f"Saved embedding cache with {len(self.cache)} entries")

        except Exception as e:
            logger.error(f"Failed to save embedding cache: {e}")

    def _generate_cache_key(self, text: str, model_name: str = "default") -> str:
        """Generate cache key from text and model"""
        # Normalize text for consistent caching
        normalized_text = text.strip().lower()

        # Create hash from text + model name
        cache_input = f"{model_name}:{normalized_text}"
        return hashlib.sha256(cache_input.encode()).hexdigest()

    def get_embedding(self, text: str, model_name: str = "default") -> Optional[np.ndarray]:
        """Get cached embedding if available"""
        if not text or len(text) < 5:  # Skip very short texts
            return None

        cache_key = self._generate_cache_key(text, model_name)

        if cache_key in self.cache:
            # Update access time
            self.metadata["access_times"][cache_key] = time.time()
            logger.debug(f"Cache hit for text: {text[:50]}...")
            return self.cache[cache_key]

        logger.debug(f"Cache miss for text: {text[:50]}...")
        return None

    def set_embedding(self, text: str, embedding: np.ndarray, model_name: str = "default"):
        """Cache an embedding"""
        if not text or embedding is None or len(text) < 5:
            return

        cache_key = self._generate_cache_key(text, model_name)

        # Check cache size and evict if necessary
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()

        # Store embedding
        self.cache[cache_key] = embedding
        current_time = time.time()
        self.metadata["creation_times"][cache_key] = current_time
        self.metadata["access_times"][cache_key] = current_time
        self.metadata["text_lengths"][cache_key] = len(text)

        logger.debug(f"Cached embedding for text: {text[:50]}...")

        # Save to disk periodically
        if len(self.cache) % 50 == 0:  # Save every 50 new entries
            self._save_cache()

    def get_embeddings_batch(self, texts: List[str], model_name: str = "default") -> Dict[str, Optional[np.ndarray]]:
        """Get multiple embeddings in batch"""
        results = {}
        cache_hits = 0

        for text in texts:
            embedding = self.get_embedding(text, model_name)
            results[text] = embedding
            if embedding is not None:
                cache_hits += 1

        if texts:
            hit_rate = cache_hits / len(texts) * 100
            logger.info(f"Batch cache hit rate: {hit_rate:.1f}% ({cache_hits}/{len(texts)})")

        return results

    def set_embeddings_batch(self, text_embedding_pairs: List[tuple], model_name: str = "default"):
        """Cache multiple embeddings in batch"""
        for text, embedding in text_embedding_pairs:
            self.set_embedding(text, embedding, model_name)

    def _evict_oldest(self):
        """Evict oldest accessed entries"""
        if not self.metadata["access_times"]:
            return

        # Find 10% oldest entries to evict
        num_to_evict = max(1, len(self.cache) // 10)
        oldest_keys = sorted(self.metadata["access_times"].items(),
                           key=lambda x: x[1])[:num_to_evict]

        for key, _ in oldest_keys:
            if key in self.cache:
                del self.cache[key]
            if key in self.metadata["access_times"]:
                del self.metadata["access_times"][key]
            if key in self.metadata["creation_times"]:
                del self.metadata["creation_times"][key]
            if key in self.metadata["text_lengths"]:
                del self.metadata["text_lengths"][key]

        logger.debug(f"Evicted {num_to_evict} old cache entries")

    def clear(self):
        """Clear all cached embeddings"""
        self.cache.clear()
        self.metadata = {"access_times": {}, "creation_times": {}, "text_lengths": {}}

        # Remove cache files
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove cache files: {e}")

        logger.info("Embedding cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        if not self.cache:
            return {"total_entries": 0}

        text_lengths = list(self.metadata["text_lengths"].values())
        creation_times = list(self.metadata["creation_times"].values())

        return {
            "total_entries": len(self.cache),
            "max_size": self.max_cache_size,
            "cache_dir": str(self.cache_dir),
            "avg_text_length": sum(text_lengths) / len(text_lengths) if text_lengths else 0,
            "oldest_entry": min(creation_times) if creation_times else None,
            "newest_entry": max(creation_times) if creation_times else None,
            "cache_size_mb": self._estimate_cache_size_mb()
        }

    def _estimate_cache_size_mb(self) -> float:
        """Estimate cache size in MB"""
        try:
            if self.cache_file.exists():
                size_bytes = self.cache_file.stat().st_size
                return size_bytes / (1024 * 1024)
        except:
            pass
        return 0.0

    def __del__(self):
        """Save cache when object is destroyed"""
        try:
            if hasattr(self, 'cache_file') and hasattr(self, 'cache') and hasattr(self, 'metadata'):
                import pickle
                import json
                try:
                    with self.cache_file.open('wb') as f:
                        pickle.dump(self.cache, f)
                    with self.metadata_file.open('w') as f:
                        json.dump(self.metadata, f, indent=2)
                except:
                    pass
        except:
            pass

# Global embedding cache instance
embedding_cache = EmbeddingCache()