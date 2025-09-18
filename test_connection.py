from src.llm_handler import LLMHandler

print("Testing LangChain + Ollama connection with Gemma...")
handler = LLMHandler()
if handler.test_connection():
    print("Testing a simple query...")
    response = handler.generate_response("What is 2+2? Give a brief answer.")
    print(f"Response: {response}")
