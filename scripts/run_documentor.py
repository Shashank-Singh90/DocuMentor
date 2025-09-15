#!/usr/bin/env python3
"""
Quick launcher - thrown together for demo
TODO: Make this proper
"""
import os
import sys
import time
import subprocess

print("Starting DocuMentor...")

# Hardcoded paths - sue me
OLLAMA_PATH = r"D:\ollama\ollama.exe"  # Windows specific!
PROJECT_PATH = r"D:\Development\Projects\Frontend"

# Check if Ollama running (hacky but works)
try:
    import requests
    requests.get("http://localhost:11434/api/tags", timeout=1)
    print("✓ Ollama already running")
except:
    print("Starting Ollama...")
    if os.name == 'nt':  # Windows
        subprocess.Popen([OLLAMA_PATH, "serve"], shell=True)
    else:
        subprocess.Popen(["ollama", "serve"])
    time.sleep(5)  # Give it time

# Start API server
print("Starting API...")
api_proc = subprocess.Popen([sys.executable, "api_server.py"])
time.sleep(3)  # More magic numbers

# Start Streamlit
print("Starting UI...")
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])




