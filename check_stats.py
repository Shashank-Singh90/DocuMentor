import requests
import json

# Check what stats endpoint returns
response = requests.get("http://localhost:8000/stats")
print("Stats Response:")
print(json.dumps(response.json(), indent=2))

# Also test the health endpoint
health = requests.get("http://localhost:8000/health")
print("\nHealth Response:")
print(json.dumps(health.json(), indent=2))

# Test sources endpoint if it exists
try:
    sources = requests.get("http://localhost:8000/sources")
    if sources.status_code == 200:
        print("\nSources Response:")
        print(json.dumps(sources.json(), indent=2))
except:
    print("\n/sources endpoint not available")