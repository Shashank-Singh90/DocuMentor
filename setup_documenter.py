#!/usr/bin/env python3
"""
Complete setup script for DocuMentor
This will install all dependencies and verify the setup
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n📌 {description}...")
    try:
        if isinstance(cmd, str):
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {description} - Success")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {description} - Failed")
            if result.stderr:
                print(result.stderr)
            return False
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    print("🚀 DocuMentor Complete Setup")
    print("=" * 50)
    
    # Check Python version
    print(f"Python version: {sys.version}")
    
    # Install packages
    packages = [
        "chromadb==0.4.22",
        "sentence-transformers==2.2.2",
        "torch>=2.0.0",
        "numpy==1.24.3",
        "pandas==2.0.3",
        "beautifulsoup4==4.12.2",
        "aiohttp==3.9.1",
        "requests==2.31.0",
        "python-multipart==0.0.6",
        "loguru==0.7.2",
        "fastapi==0.109.0",
        "uvicorn[standard]==0.27.0",
        "python-dotenv==1.0.0",
        "transformers>=4.30.0"
    ]
    
    print("\n📦 Installing required packages...")
    for package in packages:
        run_command(f"{sys.executable} -m pip install {package}", f"Installing {package.split('=')[0]}")
    
    # Verify imports
    print("\n🔍 Verifying imports...")
    try:
        import chromadb
        print("✅ ChromaDB imported successfully")
    except ImportError:
        print("❌ ChromaDB import failed")
    
    try:
        import sentence_transformers
        print("✅ Sentence Transformers imported successfully")
    except ImportError:
        print("❌ Sentence Transformers import failed")
    
    try:
        import torch
        print(f"✅ PyTorch imported successfully (CUDA available: {torch.cuda.is_available()})")
    except ImportError:
        print("❌ PyTorch import failed")
    
    # Check Ollama
    print("\n🤖 Checking Ollama...")
    run_command("ollama --version", "Ollama version check")
    run_command("ollama list", "List Ollama models")
    
    # Create necessary directories
    print("\n📁 Creating directories...")
    dirs = ["data", "data/vectordb", "data/scraped", "logs", "frontend"]
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created {dir_path}")
    
    print("\n✨ Setup complete!")
    print("\nNext steps:")
    print("1. Run: python test_llama4_integration.py")
    print("2. Run: python api_server.py")
    print("3. Visit: http://localhost:8000/docs")

if __name__ == "__main__":
    main()
