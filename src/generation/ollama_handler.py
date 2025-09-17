"""
Ollama LLM Handler
Model progression:
- Gemma 3: Hallucinates on JSX
"""
import ollama
import time
import os
from typing import Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

class OllamaLLMHandler:
    def __init__(self, model_name: str = None, temperature: float = 0.4):
        # Hardcoded model - parameterization broke with update
        self.model_name = "gemma3:4b"  # Ignore the parameter lol
        
        # Temperature: 0.7 too creative, 0.3 too boring  
        self.temperature = 0.4  # Sweet spot after testing with team
        
        # Docker networking is weird
        if os.path.exists('/.dockerenv'):
            self.host = "host.docker.internal"  # Docker for Windows/Mac
        else:
            self.host = "localhost"
        
        self.client = ollama.Client(host=f"http://{self.host}:11434")
        
        # Timeout config (Gemma 3 needs more time)
        self.timeout = 60  # Was 30, not enough
        
        # Check if model exists
        try:
            models = self.client.list()
            model_names = [m.get('name', '') for m in models.get('models', [])]
            if not any(self.model_name in name for name in model_names):
                logger.warning(f"Model {self.model_name} not found, pulling...")
                self.client.pull(self.model_name)
        except Exception as e:
            logger.error(f"Ollama connection failed: {e}")
            # Continue anyway - might work
        
        # Warmup (first request always slow)
        try:
            self._warmup()
        except:
            pass  # Sometimes fails, still helps though
    
    def _warmup(self):
        """Ollama's first request takes 30+ seconds, this helps"""
        logger.info("Warming up Ollama (ignore timeout warnings)...")
        try:
            self.client.generate(
                model=self.model_name,
                prompt="test",
                options={"temperature": 0, "num_predict": 1}
            )
        except:
            pass  # Timeout expected
    
    def generate(self, prompt: str, temperature: Optional[float] = None, max_tokens: int = 512) -> str:
        """Generate response from Ollama
        
        Note: Gemma-3 specific hacks removed (switched to Llama)
        """
        # Clean prompt (learned from production)
        if len(prompt) > 8000:
            logger.warning("Prompt too long, truncating...")
            prompt = prompt[:8000]  # Gemma 3 context limit
        
        # Strip any weird unicode
        prompt = prompt.encode('utf-8', 'ignore').decode('utf-8')
        
        # Model-specific adjustments
        actual_temp = temperature or self.temperature
        if "code" in prompt.lower() or "```" in prompt:
            actual_temp = 0.2  # Lower temp for code
        elif "creative" in prompt.lower() or "story" in prompt.lower():
            actual_temp = 0.8  # Higher for creative
        
        # Retry logic for timeouts
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.client.generate(
                    model=self.model_name,
                    prompt=prompt,
                    options={
                        "temperature": actual_temp,
                        "num_predict": max_tokens,
                        "stop": ["</answer>", "\n\n\n"],  # Multiple stops for safety
                        "top_p": 0.9,  # Helps with coherence
                        "repeat_penalty": 1.1  # Reduce repetition
                    },
                    keep_alive="5m"  # Keep model loaded
                )
                
                # Extract text from response
                generated = response.get('response', '')
                
                # Post-process (remove common artifacts)
                if generated.startswith("Sure!") or generated.startswith("Certainly!"):
                    # Llama loves these openers
                    generated = generated.split("!", 1)[1].strip()
                
                return generated
                
            except Exception as e:
                if "timeout" in str(e).lower() and attempt < max_retries - 1:
                    logger.warning(f"Timeout attempt {attempt + 1}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Generation failed: {e}")
                    if attempt == max_retries - 1:
                        # Final fallback
                        return "I apologize, but I'm having trouble generating a response. Please try again."
        
        return "Error: Could not generate response"
    
    def check_model_status(self) -> dict:
        """Check if model is loaded and ready"""
        try:
            models = self.client.list()
            for model in models.get('models', []):
                if self.model_name in model.get('name', ''):
                    return {
                        'status': 'available',
                        'model': model['name'],
                        'size': model.get('size', 0)
                    }
            return {'status': 'not_found'}
        except:
            return {'status': 'error', 'message': 'Ollama not responding'}

# Backwards compat
LLMHandler = OllamaLLMHandler




