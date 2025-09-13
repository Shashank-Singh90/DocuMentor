from src.generation.ollama_handler import OllamaLLMHandler
from src.utils.logger import get_logger

logger = get_logger(__name__)

print("🧪 Testing Gemma 3 Integration...")
print("=" * 50)

# Initialize handler with Gemma 3
handler = OllamaLLMHandler(model_name="gemma3:4b")

# Check status
status = handler.check_model_status()
print(f"📊 Gemma 3 Status: {status}")

# Test question
test_question = "Explain how to create a REST API with FastAPI"
mock_results = [{
    'content': 'FastAPI is a modern web framework for building APIs with Python 3.7+ based on standard Python type hints.',
    'metadata': {'source': 'fastapi', 'title': 'FastAPI Introduction', 'url': 'https://fastapi.tiangolo.com/'},
    'score': 0.9
}]

print(f"\n🔍 Question: {test_question}")
print("🔄 Generating answer...")

answer = handler.generate_answer(test_question, mock_results)
print(f"📝 Answer: {answer}")
print("\n✅ Test completed!")
