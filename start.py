#!/usr/bin/env python3
"""
Simplified Railway startup script for DocuMentor
"""
import os
import sys
import subprocess
from pathlib import Path

def setup_environment():
    """Setup environment for Railway"""
    # Create necessary directories
    dirs = ["data", "logs"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Set environment variables
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    
    print("✅ Environment setup complete")

def run_streamlit():
    """Run Streamlit UI"""
    port = os.environ.get("PORT", "8080")
    
    cmd = [
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false"
    ]
    
    print(f"🚀 Starting DocuMentor on port {port}")
    subprocess.run(cmd)

def main():
    """Main startup function"""
    print("🧠 DocuMentor - Starting on Railway")
    
    # Setup environment
    setup_environment()
    
    # Run Streamlit
    run_streamlit()

if __name__ == "__main__":
    main()




