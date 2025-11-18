"""
Enhanced LLM Handler with Multiple Provider Support
Supports Ollama, OpenAI, and Google Gemini
"""

import os
from typing import List, Dict, Optional, Generator
from abc import ABC, abstractmethod

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from rag_system.core.utils.logger import get_logger
from rag_system.config.settings import get_settings

logger = get_logger(__name__)
settings = get_settings()

class BaseLLMProvider(ABC):
    """Base class for LLM providers"""

    @abstractmethod
    def generate_response(self, prompt: str, context: List[Dict]) -> str:
        """Generate a response based on prompt and context"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available and configured"""
        pass

class OllamaProvider(BaseLLMProvider):
    """Ollama local LLM provider"""

    def __init__(self):
        self.base_url = f"http://{settings.ollama_host}"
        self.model = settings.ollama_model

    def generate_response(self, prompt: str, context: List[Dict]) -> str:
        """Generate response using Ollama"""
        if not HAS_REQUESTS:
            return "Error: requests library not available"

        try:
            # Build context from search results
            context_text = ""
            if context:
                context_text = "\n\nContext from documents:\n"
                for i, result in enumerate(context[:3], 1):
                    content = result.get('content', '')[:500]
                    source = result.get('metadata', {}).get('title', 'Unknown')
                    context_text += f"\n{i}. From '{source}':\n{content}...\n"

            full_prompt = f"{context_text}\n\nQuestion: {prompt}\n\nAnswer based on the context above:"

            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False
                },
                timeout=settings.ollama_timeout
            )

            if response.status_code == 200:
                return response.json().get('response', 'No response generated')
            else:
                return f"Error: Ollama request failed with status {response.status_code}"

        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            return f"Error generating response: {e}"

    def is_available(self) -> bool:
        """Check if Ollama is available"""
        if not HAS_REQUESTS:
            return False

        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except (requests.RequestException, ConnectionError, TimeoutError):
            return False

class OpenAIProvider(BaseLLMProvider):
    """OpenAI GPT provider"""

    def __init__(self):
        self.api_key = settings.openai_api_key
        self.client = None
        if self.api_key and HAS_OPENAI:
            # Use OpenAI v1.x client
            self.client = openai.OpenAI(api_key=self.api_key)

    def generate_response(self, prompt: str, context: List[Dict]) -> str:
        """Generate response using OpenAI"""
        if not HAS_OPENAI:
            return "Error: OpenAI library not available"

        if not self.client:
            return "Error: OpenAI API key not configured"

        try:
            # Build context from search results
            context_text = ""
            if context:
                context_text = "Context from documents:\n"
                for i, result in enumerate(context[:3], 1):
                    content = result.get('content', '')[:800]
                    source = result.get('metadata', {}).get('title', 'Unknown')
                    context_text += f"\n{i}. From '{source}':\n{content}...\n"

            messages = [
                {
                    "role": "system",
                    "content": "You are a helpful assistant that answers questions based on provided context. If the context doesn't contain relevant information, say so and provide general guidance."
                },
                {
                    "role": "user",
                    "content": f"{context_text}\n\nQuestion: {prompt}"
                }
            ]

            # Use OpenAI v1.x API syntax
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=1000,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            return f"Error generating response with OpenAI: {e}"

    def is_available(self) -> bool:
        """Check if OpenAI is available"""
        return HAS_OPENAI and bool(self.client)

class GeminiProvider(BaseLLMProvider):
    """Google Gemini provider"""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        if self.api_key and HAS_GEMINI:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-pro')

    def generate_response(self, prompt: str, context: List[Dict]) -> str:
        """Generate response using Gemini"""
        if not HAS_GEMINI:
            return "Error: Google Generative AI library not available"

        if not self.api_key:
            return "Error: Gemini API key not configured"

        try:
            # Build context from search results
            context_text = ""
            if context:
                context_text = "Context from documents:\n"
                for i, result in enumerate(context[:3], 1):
                    content = result.get('content', '')[:800]
                    source = result.get('metadata', {}).get('title', 'Unknown')
                    context_text += f"\n{i}. From '{source}':\n{content}...\n"

            full_prompt = f"""Based on the following context, please answer the question. If the context doesn't contain relevant information, provide general guidance.

{context_text}

Question: {prompt}

Answer:"""

            response = self.model.generate_content(full_prompt)
            return response.text

        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return f"Error generating response with Gemini: {e}"

    def is_available(self) -> bool:
        """Check if Gemini is available"""
        return HAS_GEMINI and bool(self.api_key)

class CodeGenerationMixin:
    """Mixin for code generation capabilities"""

    def generate_code(self, prompt: str, language: str = "python", context: List[Dict] = None) -> str:
        """Generate code based on prompt"""
        code_prompt = f"""Generate {language} code for the following request:

Request: {prompt}

Please provide:
1. Clean, well-documented code
2. Comments explaining the logic
3. Example usage if applicable

Requirements:
- Follow best practices for {language}
- Include error handling where appropriate
- Make the code production-ready

Code:"""

        return self.generate_response(code_prompt, context or [])

    def explain_code(self, code: str, language: str = "python") -> str:
        """Explain provided code"""
        explain_prompt = f"""Please explain the following {language} code:

```{language}
{code}
```

Provide:
1. Overview of what the code does
2. Explanation of key functions/methods
3. Any potential improvements
4. How to use it

Explanation:"""

        return self.generate_response(explain_prompt, [])

class EnhancedLLMHandler(CodeGenerationMixin):
    """Enhanced LLM handler with multiple provider support"""

    def __init__(self):
        self.providers = {
            'ollama': OllamaProvider(),
            'openai': OpenAIProvider(),
            'gemini': GeminiProvider()
        }

        self.current_provider = settings.default_llm_provider
        logger.info(f"Enhanced LLM Handler initialized with provider: {self.current_provider}")

    def set_provider(self, provider_name: str) -> bool:
        """Set the active LLM provider"""
        if provider_name not in self.providers:
            logger.error(f"Unknown provider: {provider_name}")
            return False

        if not self.providers[provider_name].is_available():
            logger.error(f"Provider {provider_name} is not available")
            return False

        self.current_provider = provider_name
        logger.info(f"Switched to provider: {provider_name}")
        return True

    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        available = []
        for name, provider in self.providers.items():
            if provider.is_available():
                available.append(name)
        return available

    def generate_answer(self, question: str, search_results: List[Dict]) -> str:
        """Generate answer using the current provider"""
        provider = self.providers.get(self.current_provider)

        if not provider:
            return f"Error: Provider {self.current_provider} not found"

        if not provider.is_available():
            # Try to fallback to an available provider
            available_providers = self.get_available_providers()
            if available_providers:
                fallback_provider = available_providers[0]
                logger.warning(f"Provider {self.current_provider} unavailable, using {fallback_provider}")
                provider = self.providers[fallback_provider]
            else:
                return "Error: No LLM providers are available"

        return provider.generate_response(question, search_results)

    def generate_response(self, prompt: str, context: List[Dict]) -> str:
        """Generate response (for CodeGenerationMixin compatibility)"""
        return self.generate_answer(prompt, context)

    def get_provider_status(self) -> Dict[str, bool]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = provider.is_available()
        return status

# Global instance
enhanced_llm_handler = EnhancedLLMHandler()