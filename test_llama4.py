from src.generation.ollama_handler import OllamaLLMHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Initialize handler
handler = OllamaLLMHandler(model_name="llama4:latest")

# Check status
status = handler.check_model_status()
print(f"Model Status: {status}")

# Test multimodal capabilities
test_question = "Explain how to create a REST API with FastAPI"
mock_results = [{
    'content': 'FastAPI is a modern web framework for building APIs with Python',
    'metadata': {'source': 'fastapi', 'title': 'FastAPI Intro'},
    'score': 0.9
}]

answer = handler.generate_answer(test_question, mock_results)
print(f"\nQuestion: {test_question}")
print(f"Answer: {answer}")
