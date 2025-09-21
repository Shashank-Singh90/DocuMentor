"""
Response Caching System for DocuMentor
Caches LLM responses to improve performance
"""
import hashlib
import json
import time
from typing import Dict, Optional, Any
from pathlib import Path
import pickle
from rag_system.core.utils.logger import get_logger

logger = get_logger(__name__)

class ResponseCache:
    """Cache for LLM responses to improve performance"""

    def __init__(self, cache_dir: str = "./data/cache", max_cache_size: int = 1000):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_cache_size = max_cache_size
        self.cache_file = self.cache_dir / "response_cache.pkl"
        self.metadata_file = self.cache_dir / "cache_metadata.json"

        # Load existing cache
        self.cache = self._load_cache()
        self.metadata = self._load_metadata()

        logger.info(f"Response cache initialized with {len(self.cache)} entries")

    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
        return {}

    def _load_metadata(self) -> Dict:
        """Load cache metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load cache metadata: {e}")
        return {"access_times": {}, "creation_times": {}}

    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f)

            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    def _generate_cache_key(self, query: str, search_results: list) -> str:
        """Generate cache key from query and search results"""
        # Normalize query
        normalized_query = query.lower().strip()

        # Create hash from query + top search result content
        content_hash = ""
        if search_results:
            # Use content of top 3 results for cache key
            top_content = [r.get('content', '')[:200] for r in search_results[:3]]
            content_hash = hashlib.md5(''.join(top_content).encode()).hexdigest()[:8]

        # Combine query and content hash
        cache_input = f"{normalized_query}_{content_hash}"
        return hashlib.md5(cache_input.encode()).hexdigest()

    def get(self, query: str, search_results: list) -> Optional[str]:
        """Get cached response if available"""
        cache_key = self._generate_cache_key(query, search_results)

        if cache_key in self.cache:
            # Update access time
            self.metadata["access_times"][cache_key] = time.time()
            logger.debug(f"Cache hit for query: {query[:50]}...")
            return self.cache[cache_key]

        logger.debug(f"Cache miss for query: {query[:50]}...")
        return None

    def set(self, query: str, search_results: list, response: str):
        """Cache a response"""
        if not response or len(response) < 10:  # Don't cache very short responses
            return

        cache_key = self._generate_cache_key(query, search_results)

        # Check cache size and evict if necessary
        if len(self.cache) >= self.max_cache_size:
            self._evict_oldest()

        # Store response
        self.cache[cache_key] = response
        current_time = time.time()
        self.metadata["creation_times"][cache_key] = current_time
        self.metadata["access_times"][cache_key] = current_time

        logger.debug(f"Cached response for query: {query[:50]}...")

        # Save to disk periodically
        if len(self.cache) % 10 == 0:  # Save every 10 new entries
            self._save_cache()

    def _evict_oldest(self):
        """Evict oldest accessed entry"""
        if not self.metadata["access_times"]:
            return

        # Find oldest accessed entry
        oldest_key = min(self.metadata["access_times"],
                        key=self.metadata["access_times"].get)

        # Remove from cache and metadata
        if oldest_key in self.cache:
            del self.cache[oldest_key]
        if oldest_key in self.metadata["access_times"]:
            del self.metadata["access_times"][oldest_key]
        if oldest_key in self.metadata["creation_times"]:
            del self.metadata["creation_times"][oldest_key]

        logger.debug(f"Evicted old cache entry")

    def clear(self):
        """Clear all cache"""
        self.cache.clear()
        self.metadata = {"access_times": {}, "creation_times": {}}

        # Remove cache files
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
            if self.metadata_file.exists():
                self.metadata_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to remove cache files: {e}")

        logger.info("Cache cleared")

    def get_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            "total_entries": len(self.cache),
            "max_size": self.max_cache_size,
            "cache_dir": str(self.cache_dir),
            "oldest_entry": min(self.metadata["creation_times"].values()) if self.metadata["creation_times"] else None,
            "newest_entry": max(self.metadata["creation_times"].values()) if self.metadata["creation_times"] else None
        }

    def __del__(self):
        """Save cache when object is destroyed"""
        try:
            if hasattr(self, 'cache_file') and hasattr(self, 'cache') and hasattr(self, '_save_cache'):
                # Use Path objects that have been cached
                if hasattr(self, 'cache') and hasattr(self, 'metadata'):
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

# Global cache instance
response_cache = ResponseCache()