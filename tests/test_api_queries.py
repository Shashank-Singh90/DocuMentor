import requests
import json

# API base URL
API_URL = "http://localhost:8000"

def test_api():
    print("🧪 Testing DocuMentor API with Llama 4\n")
    
    # Test 1: Ask a question
    print("1️⃣ Testing /ask endpoint...")
    response = requests.post(f"{API_URL}/ask", json={
        "question": "How do I create a FastAPI application with authentication?",
        "k": 5,
        "temperature": 0.1
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Answer received in {data['response_time']:.2f}s")
        print(f"Answer preview: {data['answer'][:200]}...")
        print(f"Sources used: {len(data['sources'])}")
        print(f"Confidence: {data['confidence']:.2%}\n")
    else:
        print(f"❌ Error: {response.status_code}\n")
    
    # Test 2: Search documentation
    print("2️⃣ Testing /search endpoint...")
    response = requests.post(f"{API_URL}/search", json={
        "query": "React hooks",
        "k": 3
    })
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Found {data['total_found']} results")
        for i, result in enumerate(data['results'][:3], 1):
            print(f"   {i}. {result['metadata']['source']} - {result['metadata'].get('title', 'N/A')}")
        print()
    
    # Test 3: Get stats
    print("3️⃣ Testing /stats endpoint...")
    response = requests.get(f"{API_URL}/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print(f"✅ System Stats:")
        print(f"   Total documents: {stats['total_documents']}")
        print(f"   Sources: {', '.join(stats['sources'])}")
        print(f"   Model: {stats['llm_model']}")
        print(f"   Status: {stats['status']}")

if __name__ == "__main__":
    test_api()




