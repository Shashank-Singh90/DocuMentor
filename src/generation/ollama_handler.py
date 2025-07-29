import requests
import json
from typing import List, Dict, Optional
from src.utils.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

class OllamaLLMHandler:
    """
    Advanced LLM handler using Ollama for local AI inference
    """
    
    def __init__(self, model_name: str = "llama3.2:3b", ollama_url: str = "http://localhost:11434"):
        """Initialize Ollama LLM handler"""
        self.model_name = model_name
        self.ollama_url = ollama_url
        self.api_url = f"{ollama_url}/api/generate"
        
        logger.info(f"🤖 Initializing Ollama LLM Handler with model: {model_name}")
        
        # Test connection
        if self._test_connection():
            logger.info("✅ Ollama connection successful!")
        else:
            logger.warning("⚠️ Ollama not available, falling back to simple responses")
            self.ollama_available = False
        
    def _test_connection(self) -> bool:
        """Test if Ollama is running and model is available"""
        try:
            # Test if Ollama is running
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [model['name'] for model in models]
                
                if self.model_name in model_names:
                    self.ollama_available = True
                    return True
                else:
                    logger.warning(f"⚠️ Model {self.model_name} not found. Available models: {model_names}")
                    return False
            return False
        except Exception as e:
            logger.warning(f"⚠️ Could not connect to Ollama: {e}")
            return False
    
    def generate_answer(
        self,
        question: str,
        search_results: List[Dict],
        max_tokens: int = 512,
        temperature: float = 0.1
    ) -> str:
        """Generate answer using Ollama LLM"""
        
        if not hasattr(self, 'ollama_available') or not self.ollama_available:
            return self._fallback_response(question, search_results)
        
        # Prepare context from search results
        context = self._prepare_context(search_results)
        
        # Create the prompt
        prompt = self._create_prompt(question, context)
        
        try:
            # Call Ollama API
            response = requests.post(
                self.api_url,
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                        "top_p": 0.9,
                        "stop": ["Human:", "Assistant:", "Question:", "Context:"]
                    }
                },
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                answer = result.get('response', '').strip()
                
                if answer:
                    # Add source citations
                    return self._add_citations(answer, search_results)
                else:
                    logger.warning("⚠️ Empty response from Ollama")
                    return self._fallback_response(question, search_results)
            else:
                logger.error(f"❌ Ollama API error: {response.status_code}")
                return self._fallback_response(question, search_results)
                
        except Exception as e:
            logger.error(f"❌ Error calling Ollama: {e}")
            return self._fallback_response(question, search_results)
    
    def _prepare_context(self, search_results: List[Dict]) -> str:
        """Prepare context from search results"""
        if not search_results:
            return "No relevant documentation found."
        
        context_parts = []
        for i, result in enumerate(search_results[:5], 1):  # Use top 5 results
            content = result.get('content', '').strip()
            metadata = result.get('metadata', {})
            source = metadata.get('source', 'unknown')
            title = metadata.get('title', 'Unknown')
            
            if content:
                # Truncate very long content
                if len(content) > 1000:
                    content = content[:1000] + "..."
                
                context_parts.append(f"[Source {i}: {source.upper()} - {title}]\n{content}")
        
        return "\n\n".join(context_parts)
    
    def _create_prompt(self, question: str, context: str) -> str:
        """Create a well-structured prompt for the LLM"""
        prompt = f"""You are DocuMentor, an expert AI assistant specializing in software documentation. Your job is to provide helpful, accurate, and well-structured answers based on the provided documentation context.

Context from Documentation:
{context}

Question: {question}

Instructions:
1. Answer the question based ONLY on the provided context
2. If the context doesn't contain enough information, say so clearly
3. Provide specific examples or code snippets when available in the context
4. Structure your response with clear headings and bullet points when appropriate
5. Be concise but comprehensive
6. If mentioning specific features or functions, reference which documentation source they come from

Answer:"""
        
        return prompt
    
    def _add_citations(self, answer: str, search_results: List[Dict]) -> str:
        """Add source citations to the answer"""
        if not search_results:
            return answer
        
        # Add sources section
        sources_section = "\n\n**📚 Sources:**\n"
        for i, result in enumerate(search_results[:3], 1):  # Show top 3 sources
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
                    return f"I found information about '{question}' but couldn't generate a detailed response. Please check the sources below."
        logger.info("🔄 Using fallback simple LLM handler")
        simple_handler = SimpleLLMHandler()
        return simple_handler.generate_answer(question, search_results)
    
    def check_model_status(self) -> Dict:
        """Check the status of the Ollama model"""
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
                            'modified': model.get('modified_at', '')
                        }
                
                return {
                    'status': 'model_not_found',
                    'available_models': [m['name'] for m in models]
                }
            else:
                return {'status': 'ollama_not_running'}
                
        except Exception as e:
            return {'status': 'connection_error', 'error': str(e)}

# Test function
def test_ollama_handler():
    """Test the Ollama LLM handler"""
    logger.info("🧪 Testing OllamaLLMHandler...")
    
    handler = OllamaLLMHandler()
    
    # Check model status
    status = handler.check_model_status()
    logger.info(f"📊 Model status: {status}")
    
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
    logger.info("✅ Ollama handler test completed!")

if __name__ == "__main__":
    test_ollama_handler()