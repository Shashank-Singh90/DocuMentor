#!/usr/bin/env python3
"""
Quick launcher - thrown together for demo
TODO: Make this proper
Author: Mike (Jan 2024)
Updated: Sept 2024 (added retry logic)
"""
import os
import sys
import time
import subprocess
import psutil  # Added for process checking

print("=" * 50)
print("Starting DocuMentor v0.4.2")
print("=" * 50)

# Hardcoded paths - sue me
OLLAMA_PATH = r"D:\ollama\ollama.exe"  # Windows specific!
PROJECT_PATH = r"D:\Development\Projects\Frontend"

# Change to project directory
os.chdir(PROJECT_PATH)
print(f"Working directory: {os.getcwd()}")

# Check if Ollama running (hacky but works)
ollama_running = False
for proc in psutil.process_iter(['name']):
    if 'ollama' in proc.info['name'].lower():
        ollama_running = True
        break

if not ollama_running:
    print("Starting Ollama...")
    if os.name == 'nt':  # Windows
        # Start in background
        subprocess.Popen([OLLAMA_PATH, "serve"], 
                        shell=True, 
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(["ollama", "serve"])
    
    # Wait for Ollama to start (magic sleep)
    print("Waiting for Ollama to start...")
    time.sleep(5)  # Usually enough
    
    # Verify it's running
    import requests
    for i in range(10):  # Try 10 times
        try:
            requests.get("http://localhost:11434/api/tags", timeout=1)
            print("✓ Ollama is running")
            break
        except:
            time.sleep(1)
    else:
        print("⚠ Ollama might not be running properly")
else:
    print("✓ Ollama already running")

# Pull model if needed (this takes forever first time)
print("Checking Llama 3.2 model...")
try:
    result = subprocess.run(["ollama", "list"], 
                          capture_output=True, 
                          text=True, 
                          timeout=5)
    if "llama3.2" not in result.stdout:
        print("Pulling llama3.2 model (this will take a while)...")
        subprocess.run(["ollama", "pull", "llama3.2"])
except:
    print("Could not check model - continuing anyway")

# Start API server
print("\nStarting API server...")
api_proc = subprocess.Popen([sys.executable, "api_server.py"])
time.sleep(3)  # Give it time to start

# Test API
try:
    import requests
    response = requests.get("http://localhost:8000/health")
    if response.json()["status"] == "ok":
        print("✓ API server is running")
except:
    print("⚠ API server might not be ready")

# Start Streamlit
print("\nStarting Streamlit UI...")
print("Access the app at: http://localhost:8501")
print("-" * 50)
print("Press Ctrl+C to stop all services")
print("-" * 50)

try:
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
except KeyboardInterrupt:
    print("\nShutting down...")
    api_proc.terminate()
    print("Goodbye!")