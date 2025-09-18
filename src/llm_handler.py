import os
from dotenv import load_dotenv
from langchain_community.llms import Ollama

load_dotenv()

class LLMHandler:
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11435')
        self.model_name = os.getenv('OLLAMA_MODEL', 'gemma2:2b')
        self.llm = self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize Ollama LLM with quality-preserving optimizations"""
        return Ollama(
            model=self.model_name,
            base_url=self.base_url,
            # Quality-preserving efficiency settings
            num_ctx=2048,          # Good context window
            temperature=0.7,       # Balanced creativity
            top_p=0.9,            # Quality sampling
            top_k=40,             # Focused vocabulary
            repeat_penalty=1.1,    # Prevents repetition
        )
    
    def quality_check_response(self, response: str, min_length: int = 20) -> bool:
        """Check if response meets quality standards"""
        if len(response.strip()) < min_length:
            return False
        if response.lower().startswith("error"):
            return False
        return True
    
    def generate_response(self, prompt: str) -> str:
        """Generate response with quality assurance"""
        try:
            # Reasonable prompt length limit
            if len(prompt) > 2000:
                prompt = prompt[:2000] + "..."
            
            response = self.llm.invoke(prompt)
            
            # Quality check - retry if response is too short
            if not self.quality_check_response(response):
                response = self.llm.invoke(f"Please provide a detailed answer: {prompt}")
            
            return response
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def test_connection(self):
        """Test if Ollama is running and model is available"""
        try:
            response = self.llm.invoke("Hello! Please confirm you are working properly.")
            print(f"✅ Connection successful! Response: {response}")
            return True
        except Exception as e:
            print(f"❌ Connection failed: {str(e)}")
            return False
