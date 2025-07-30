#!/usr/bin/env python3
"""
Railway startup script for DocuMentor
Handles both Streamlit UI and FastAPI backend
"""
import os
import sys
import subprocess
import threading
import time
from pathlib import Path

def run_streamlit():
    """Run Streamlit UI"""
    port = os.environ.get("PORT", "8080")
    cmd = [
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.serverAddress", "0.0.0.0",
        "--browser.gatherUsageStats", "false",
        "--server.enableCORS", "false",
        "--server.enableWebsocketCompression", "false"
    ]
    
    print(f"🚀 Starting Streamlit on port {port}")
    subprocess.run(cmd)

def setup_environment():
    """Setup environment for Railway"""
    # Create necessary directories
    dirs = ["data/models", "data/vectordb", "data/raw", "data/processed", "logs"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Set default environment variables
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    
    print("✅ Environment setup complete")

def main():
    """Main startup function"""
    print("🧠 DocuMentor - Starting on Railway")
    
    # Setup environment
    setup_environment()
    
    # Run Streamlit
    print("🎨 Starting Streamlit UI")
    run_streamlit()

if __name__ == "__main__":
    main()