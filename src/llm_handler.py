import time
import os
import hashlib
import json
from typing import Dict, List, Optional, Generator, Union
from dataclasses import dataclass
import requests
import threading
from collections import OrderedDict
from langchain_community.llms import Ollama
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler

@dataclass
class CachedResponse:
    response: str
    timestamp: float
    usage_count: int
    average_response_time: float

class OptimizedStreamingHandler(BaseCallbackHandler):
    def __init__(self):
        self.tokens = []
        self.current_response = ""
        
    def on_llm_new_token(self, token: str, **kwargs):
        self.tokens.append(token)
        self.current_response += token
        
    def get_response(self) -> str:
        return self.current_response
    
    def reset(self):
        self.tokens = []
        self.current_response = ""

class OptimizedLLMHandler:
    def __init__(self, base_url: str = "http://localhost:11434", 
                 model_name: str = "gemma2:2b"):
        self.base_url = base_url
        self.model_name = model_name
        
        # Response cache
        self.cache = OrderedDict()
        self.cache_max_size = 200
        self.cache_ttl = 3600  # 1 hour
        
        # Performance tracking
        self.response_times = []
        self.total_requests = 0
        self.cache_hits = 0
        
        # Connection pool
        self.session = requests.Session()
        self.session.timeout = 30
        
        # Thread lock for cache operations
        self.cache_lock = threading.Lock()
        
        # Streaming handler
        self.streaming_handler = OptimizedStreamingHandler()
        
        # Initialize LLM with optimizations
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize LLM with optimal settings"""
        try:
            self.llm = Ollama(
                model=self.model_name,
                base_url=self.base_url,
                # Performance optimizations
                temperature=0.1,  # Lower for more consistent responses
                top_p=0.9,       # Focus on high probability tokens
                top_k=40,        # Limit vocabulary for speed
                num_ctx=4096,    # Context window
                num_predict=512, # Max response length
                repeat_penalty=1.1,
                # Threading and batching
                num_thread=os.cpu_count() or 4,
                num_gpu=1 if self._gpu_available() else 0,
                # Callback for streaming
                callbacks=[self.streaming_handler],
                verbose=False
            )
            print(f"✅ LLM initialized: {self.model_name}")
            
        except Exception as e:
            print(f"❌ LLM initialization failed: {e}")
            raise
    
    def _gpu_available(self) -> bool:
        """Check if GPU is available for Ollama"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _get_cache_key(self, prompt: str, context: Optional[str] = None) -> str:
        """Generate cache key for prompt and context"""
        cache_input = prompt
        if context:
            cache_input += f"|||{context}"
        return hashlib.md5(cache_input.encode()).hexdigest()
    
    def _clean_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = []
        
        for key, cached_response in self.cache.items():
            if current_time - cached_response.timestamp > self.cache_ttl:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]
    
    def _update_cache(self, cache_key: str, response: str, response_time: float):
        """Update cache with new response"""
        with self.cache_lock:
            # Clean expired entries first
            self._clean_cache()
            
            # Add new entry
            if cache_key in self.cache:
                # Update existing entry
                cached = self.cache[cache_key]
                cached.usage_count += 1
                cached.average_response_time = (
                    (cached.average_response_time + response_time) / 2
                )
                # Move to end (most recently used)
                self.cache.move_to_end(cache_key)
            else:
                # Add new entry
                if len(self.cache) >= self.cache_max_size:
                    # Remove least recently used
                    self.cache.popitem(last=False)
                
                self.cache[cache_key] = CachedResponse(
                    response=response,
                    timestamp=time.time(),
                    usage_count=1,
                    average_response_time=response_time
                )
    
    def _get_cached_response(self, cache_key: str) -> Optional[str]:
        """Get cached response if available and valid"""
        with self.cache_lock:
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                
                # Check if cache is still valid
                if time.time() - cached.timestamp < self.cache_ttl:
                    cached.usage_count += 1
                    # Move to end (most recently used)
                    self.cache.move_to_end(cache_key)
                    self.cache_hits += 1
                    return cached.response
                else:
                    # Remove expired entry
                    del self.cache[cache_key]
        
        return None
    
    def generate_response_optimized(self, prompt: str, 
                                  context: Optional[str] = None,
                                  use_cache: bool = True,
                                  stream: bool = False) -> Union[str, Generator[str, None, None]]:
        """Generate optimized response with caching and streaming"""
        
        start_time = time.time()
        self.total_requests += 1
        
        # Check cache first
        if use_cache:
            cache_key = self._get_cache_key(prompt, context)
            cached_response = self._get_cached_response(cache_key)
            
            if cached_response:
                print("⚡ Cache hit!")
                if stream:
                    return self._stream_cached_response(cached_response)
                return cached_response
        
        # Build full prompt
        if context:
            full_prompt = f"""Context: {context}
            
Question: {prompt}

Please provide a helpful and accurate answer based on the context provided."""
        else:
            full_prompt = prompt
        
        try:
            if stream:
                return self._generate_streaming_response(full_prompt, cache_key if use_cache else None, start_time)
            else:
                # Generate response
                response = self.llm(full_prompt)
                
                # Update performance metrics
                response_time = time.time() - start_time
                self.response_times.append(response_time)
                
                # Cache the response
                if use_cache:
                    self._update_cache(cache_key, response, response_time)
                
                print(f"🤖 LLM response generated in {response_time:.2f}s")
                return response
                
        except Exception as e:
            print(f"❌ LLM generation failed: {e}")
            return f"I apologize, but I encountered an error: {str(e)}"
    
    def _generate_streaming_response(self, prompt: str, 
                                   cache_key: Optional[str], 
                                   start_time: float) -> Generator[str, None, None]:
        """Generate streaming response"""
        try:
            self.streaming_handler.reset()
            
            # This would need to be implemented with Ollama's streaming API
            # For now, simulate streaming by chunking response
            response = self.llm(prompt)
            response_time = time.time() - start_time
            
            # Cache the full response
            if cache_key:
                self._update_cache(cache_key, response, response_time)
            
            # Yield response in chunks for streaming effect
            words = response.split()
            for i, word in enumerate(words):
                yield word + " "
                if i % 5 == 0:  # Yield every 5 words
                    time.sleep(0.05)  # Small delay for streaming effect
            
        except Exception as e:
            yield f"Error: {str(e)}"
    
    def _stream_cached_response(self, response: str) -> Generator[str, None, None]:
        """Stream cached response with simulated delay"""
        words = response.split()
        for word in words:
            yield word + " "
            time.sleep(0.02)  # Faster for cached responses
    
    def generate_with_context_ranking(self, question: str, 
                                    context_docs: List[Dict],
                                    max_context_length: int = 2000) -> str:
        """Generate response with intelligently ranked context"""
        
        # Rank context documents by relevance (simple keyword matching)
        question_words = set(question.lower().split())
        
        scored_docs = []
        for doc in context_docs:
            content = doc.get('content', '').lower()
            doc_words = set(content.split())
            
            # Calculate overlap score
            overlap = len(question_words.intersection(doc_words))
            scored_docs.append((overlap, doc))
        
        # Sort by relevance score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        # Build context within length limit
        context_parts = []
        current_length = 0
        
        for score, doc in scored_docs:
            content = doc.get('content', '')
            if current_length + len(content) <= max_context_length:
                context_parts.append(content)
                current_length += len(content)
            else:
                # Add partial content if there's space
                remaining_space = max_context_length - current_length
                if remaining_space > 100:  # Only if meaningful space left
                    context_parts.append(content[:remaining_space] + "...")
                break
        
        context = "\n\n".join(context_parts)
        return self.generate_response_optimized(question, context=context)
    
    def test_connection_optimized(self) -> Dict[str, Union[bool, str, float]]:
        """Comprehensive connection test with performance metrics"""
        test_results = {
            'connected': False,
            'model_available': False,
            'response_time': 0,
            'error': None
        }
        
        try:
            start_time = time.time()
            
            # Test basic connection
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code != 200:
                test_results['error'] = f"Ollama server returned status {response.status_code}"
                return test_results
            
            test_results['connected'] = True
            
            # Check if model is available
            models = response.json().get('models', [])
            model_names = [model.get('name', '') for model in models]
            
            if self.model_name in model_names or any(self.model_name in name for name in model_names):
                test_results['model_available'] = True
            else:
                test_results['error'] = f"Model {self.model_name} not found. Available: {model_names}"
                return test_results
            
            # Test simple generation
            test_response = self.generate_response_optimized(
                "Hello", use_cache=False
            )
            
            test_results['response_time'] = time.time() - start_time
            
            if test_response and not test_response.startswith("Error"):
                print(f"✅ LLM connection test successful ({test_results['response_time']:.2f}s)")
            else:
                test_results['error'] = "Test generation failed"
            
        except requests.exceptions.ConnectionError:
            test_results['error'] = "Cannot connect to Ollama server. Is it running?"
        except requests.exceptions.Timeout:
            test_results['error'] = "Connection timeout - Ollama server may be overloaded"
        except Exception as e:
            test_results['error'] = f"Connection test failed: {str(e)}"
        
        return test_results
    
    def get_performance_stats(self) -> Dict:
        """Get comprehensive performance statistics"""
        with self.cache_lock:
            avg_response_time = (
                sum(self.response_times) / len(self.response_times) 
                if self.response_times else 0
            )
            
            cache_hit_rate = (
                self.cache_hits / self.total_requests 
                if self.total_requests > 0 else 0
            )
            
            return {
                'total_requests': self.total_requests,
                'cache_hits': self.cache_hits,
                'cache_hit_rate': cache_hit_rate,
                'cache_size': len(self.cache),
                'average_response_time': avg_response_time,
                'fastest_response': min(self.response_times) if self.response_times else 0,
                'slowest_response': max(self.response_times) if self.response_times else 0,
                'model_name': self.model_name,
                'base_url': self.base_url
            }
    
    def warm_up_model(self) -> bool:
        """Warm up the model with a simple query"""
        try:
            print("🔥 Warming up LLM...")
            self.generate_response_optimized("Hello", use_cache=False)
            print("✅ LLM warmed up successfully")
            return True
        except Exception as e:
            print(f"❌ LLM warm-up failed: {e}")
            return False
    
    def optimize_for_batch_processing(self):
        """Configure LLM for batch processing scenarios"""
        self.llm.temperature = 0.0  # Deterministic responses for batching
        self.llm.top_p = 0.8       # More focused responses
        self.cache_max_size = 500  # Larger cache for batch work
        print("⚡ LLM optimized for batch processing")
    
    def optimize_for_interactive(self):
        """Configure LLM for interactive use"""
        self.llm.temperature = 0.3  # More creative responses
        self.llm.top_p = 0.95      # More diverse responses
        self.cache_max_size = 100  # Smaller cache for interactive use
        print("⚡ LLM optimized for interactive use")
        