#!/usr/bin/env python3
"""
DocuMentor Professional Launcher - Python 3.11
"""
import sys
import time
import subprocess
import requests
import psutil
from pathlib import Path

def check_python_version():
    """Ensure we're running Python 3.11"""
    version = sys.version_info
    if version.major != 3 or version.minor != 11:
        print(f"Warning: Running Python {version.major}.{version.minor}, recommended: Python 3.11")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_dependencies():
    """Check all required dependencies"""
    print("Checking dependencies...")
    
    required_packages = [
        "fastapi", "uvicorn", "chromadb", "ollama", 
        "pydantic", "loguru", "sentence_transformers",
        "pydantic_settings"
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package}")
            missing.append(package)
    
    if missing:
        print(f"\nInstall missing packages: pip install {' '.join(missing)}")
        return False
    return True

def main():
    """Main launcher"""
    print("🚀 DocuMentor Professional Launcher (Python 3.11)")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("Consider switching to Python 3.11 for optimal compatibility")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies missing.")
        print("Install with: pip install -r requirements-production.txt")
        return
    
    print("\n✅ All dependencies found!")
    print("🌟 Starting DocuMentor...")
    print("📊 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")

if __name__ == "__main__":
    main()