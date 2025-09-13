import os
import requests
import json
from typing import List, Dict, Optional, AsyncGenerator
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class OllamaLLMHandler:
    """
    Advanced LLM handler using Ollama for local AI inference with Gemma 3
    """
    
    def __init__(self, model_name: str = None, ollama_url: str = "http://localhost:11434"):
        """Initialize Ollama LLM handler for Gemma 3"""
        # Use environment variable or default to Gemma 3
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "gemma3:4b")
        self.ollama_url = ollama_url
        self.api_url = f"{ollama_url}/api/generate"
        self.stream_url = f"{ollama_url}/api/generate"
        
        # Gemma 3 optimized parameters
        self.default_params = {
            "temperature": float(os.getenv("TEMPERATURE", "0.1")),
            "num_predict": int(os.getenv("MAX_TOKENS", "2048")),
            "top_p": float(os.getenv("TOP_P", "0.9")),
            "num_ctx": int(os.getenv("MODEL_N_CTX", "8192")),  # Gemma 3 supports 8K context
            "stop": ["Human:", "Assistant:", "Question:", "Context:", "<end_of_turn>"],
            "repeat_penalty": 1.1,
            "seed": 42
        }
        
        logger.info(f"🤖 Initializing Ollama LLM Handler with Gemma 3 model: {self.model_name}")
        
        # Test connection
        if self._test_connection():
            logger.info("✅ Ollama connection successful! Gemma 3 ready.")
        else:
            logger.warning("⚠️ Ollama not available, falling back to simple responses")
            self.ollama_available = False
    
    def _test_connection(self) -> bool:
        """Test if Ollama is running and Gemma 3 model is available"""
        try:
            # Test if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name in model_names:
                    self.ollama_available = True
                    # Get model info
                    for model in models:
                        if model['name'] == self.model_name:
                            size_gb = model.get('size', 0) / (1024**3)
                            logger.info(f"📊 Model {self.model_name} loaded - Size: {size_gb:.1f}GB")
                    return True
                else:
                    logger.warning(f"⚠️ Model {self.model_name} not found. Available models: {model_names}")
                    # Suggest Gemma 3 variants
                    logger.info("💡 To install Gemma 3, run: ollama pull gemma3:4b")
                    return False
            return False
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to Ollama: {e}")
            return False
    
    def generate_answer(
        self,
        question: str,
        search_results: List[Dict],
        max_tokens: int = None,
        temperature: float = None
    ) -> str:
        """Generate answer using Gemma 3"""
        
        if not hasattr(self, 'ollama_available') or not self.ollama_available:
            return self._fallback_response(question, search_results)
        
        # Prepare context from search results
        context = self._prepare_context(search_results)
        
        # Create the prompt optimized for Gemma 3
        prompt = self._create_gemma3_prompt(question, context)
        
        # Override default params if provided
        params = self.default_params.copy()
        if max_tokens:
            params['num_predict'] = max_tokens
        if temperature is not None:
            params['temperature'] = temperature
        
        try:
            # Call Ollama API
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": params
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                
                # Log token usage for Gemma 3
                total_duration = result.get('total_duration', 0) / 1e9  # Convert to seconds
                logger.info(f"⏱️ Gemma 3 response time: {total_duration:.2f}s")
                
                if answer:
                    # Add source citations
                    return self._add_citations(answer, search_results)
                else:
                    logger.warning("⚠️ Empty response from Gemma 3")
                    return self._fallback_response(question, search_results)
            else:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                return self._fallback_response(question, search_results)
                
        except Exception as e:
            logger.error(f"❌ Error calling Ollama: {e}")
            return self._fallback_response(question, search_results)
    
    async def generate_stream(
        self,
        prompt: str,
        max_tokens: int = None,
        temperature: float = None
    ) -> AsyncGenerator[str, None]:
        """Stream responses from Gemma 3 for lower latency"""
        params = self.default_params.copy()
        if max_tokens:
            params['num_predict'] = max_tokens
        if temperature is not None:
            params['temperature'] = temperature
        
        try:
            response = requests.post(
                self.stream_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": True,
                    "options": params
                },
                stream=True,
                timeout=120
            )
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if 'response' in data:
                        yield data['response']
                    if data.get('done', False):
                        break
                        
        except Exception as e:
            logger.error(f"❌ Error in stream generation: {e}")
            yield f"Error: {str(e)}"
    
    def _prepare_context(self, search_results: List[Dict]) -> str:
        """Prepare context from search results optimized for Gemma 3's context window"""
        if not search_results:
            return "No relevant documentation found."
        
        context_parts = []
        # Gemma 3 can handle good context, use top 6 results
        for i, result in enumerate(search_results[:6], 1):
            content = result.get('content', '').strip()
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'unknown')
            title = metadata.get('title', 'Unknown')
            
            if content:
                # Gemma 3 optimized content length
                if len(content) > 1200:
                    content = content[:1200] + "..."
                
                context_parts.append(f"[Source {i}: {source.upper()} - {title}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _create_gemma3_prompt(self, question: str, context: str) -> str:
        """Create a prompt optimized for Gemma 3's capabilities"""
        prompt = f"""<bos><start_of_turn>user
You are DocuMentor, an expert AI assistant powered by Gemma 3, specializing in software documentation. 
Your responses should be accurate, detailed, and well-structured based on the provided documentation context.

Context from Documentation:
{context}

Question: {question}<end_of_turn>
<start_of_turn>model
Based on the provided documentation, I'll help you with your question about {question}.

"""
        return prompt
    
    def _add_citations(self, answer: str, search_results: List[Dict]) -> str:
        """Add source citations to the answer"""
        if not search_results:
            return answer
        
        # Add sources section
        sources_section = "\n\n**📚 Sources:**\n"
        for i, result in enumerate(search_results[:5], 1):  # Show top 5 sources
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'unknown')
            title = metadata.get('title', 'Unknown')
            url = metadata.get('url', '#')
            score = result.get('score', 0)
            
            sources_section += f"{i}. **[{source.upper()}]** {title} (relevance: {score:.0%})\n"
        
        return answer + sources_section
    
    def _fallback_response(self, question: str, search_results: List[Dict]) -> str:
        """Fallback to simple response when Ollama is not available"""
        try:
            from src.generation.llm_handler import SimpleLLMHandler
        except ImportError:
            # Define a simple fallback class
            class SimpleLLMHandler:
                def generate_answer(self, question, search_results):
                    return f"I found information about '{question}' but Gemma 3 is not available. Please ensure Ollama is running with: ollama pull gemma3:4b"
        
        logger.info("🔄 Using fallback simple LLM handler")
        simple_handler = SimpleLLMHandler()
        return simple_handler.generate_answer(question, search_results)
    
    def check_model_status(self) -> Dict:
        """Check the status of the Gemma 3 model"""
        try:
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                
                for model in models:
                    if model['name'] == self.model_name:
                        return {
                            'status': 'available',
                            'model': self.model_name,
                            'size': model.get('size', 0),
                            'modified': model.get('modified_at', ''),
                            'family': 'Gemma 3',
                            'parameters': self._get_model_size(model['name'])
                        }
                
                # Check for any Gemma 3 models
                gemma3_models = [m['name'] for m in models if 'gemma3' in m['name']]
                if gemma3_models:
                    return {
                        'status': 'different_variant',
                        'requested': self.model_name,
                        'available_gemma3': gemma3_models
                    }
                
                return {
                    'status': 'model_not_found',
                    'available_models': [m['name'] for m in models],
                    'suggestion': 'Run: ollama pull gemma3:4b'
                }
            else:
                return {'status': 'ollama_not_running'}
                
        except Exception as e:
            return {'status': 'connection_error', 'error': str(e)}
    
    def _get_model_size(self, model_name: str) -> str:
        """Extract parameter size from model name"""
        if '2b' in model_name.lower():
            return '2 Billion'
        elif '4b' in model_name.lower():
            return '4 Billion'  # Your Gemma 3 model
        elif '7b' in model_name.lower():
            return '7 Billion'
        elif '9b' in model_name.lower():
            return '9 Billion'
        elif '27b' in model_name.lower():
            return '27 Billion'
        return 'Unknown'

# Test function
def test_gemma3_handler():
    """Test the Gemma 3 handler"""
    logger.info("🧪 Testing Gemma 3 Handler...")
    
    handler = OllamaLLMHandler()
    
    # Check model status
    status = handler.check_model_status()
    logger.info(f"📊 Gemma 3 status: {status}")
    
    # Mock search results for testing
    mock_results = [
        {
            'content': 'FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.',
            'metadata': {'source': 'fastapi', 'title': 'FastAPI Introduction', 'url': 'https://fastapi.tiangolo.com/'},
            'score': 0.85
        }
    ]
    
    # Test question
    question = "What is FastAPI and why should I use it?"
    answer = handler.generate_answer(question, mock_results)
    
    logger.info(f"🔍 Question: {question}")
    logger.info(f"📝 Answer: {answer}")
    logger.info("✅ Gemma 3 handler test completed!")

if __name__ == "__main__":
    test_gemma3_handler()
