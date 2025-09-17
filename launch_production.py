# Create professional launcher
@"
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

def check_ollama():
    """Check Ollama service"""
    print("\nChecking Ollama...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        models = response.json().get("models", [])
        model_names = [m["name"] for m in models]
        
        print(f"  ✓ Ollama running with {len(models)} models")
        
        if "gemma3:4b" in model_names or "llama3.2:3b" in model_names:
            print("  ✓ Required model available")
            return True
        else:
            print("  ⚠ Required model not found")
            return False
            
    except Exception as e:
        print(f"  ✗ Ollama connection failed: {e}")
        return False

def setup_directories():
    """Create required directories"""
    print("\nSetting up directories...")
    
    directories = [
        "data/vectordb", "data/uploads", "data/scraped", 
        "logs", "data/processed", "src/config"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✓ {directory}")

def main():
    """Main launcher"""
    print("🚀 DocuMentor Professional Launcher (Python 3.11)")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        print("Consider switching to Python 3.11 for optimal compatibility")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependencies missing. Install with:")
        print("pip install -r requirements-production.txt")
        return
    
    # Check Ollama
    ollama_ok = check_ollama()
    if not ollama_ok:
        print("⚠ Ollama issues detected - server will run with limited functionality")
    
    # Setup environment
    setup_directories()
    
    # Start server
    print("\n🌟 Starting DocuMentor Production Server...")
    print("📊 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop")
    print("-" * 50)
    
    try:
        from api_server_production import run_server
        run_server()
    except ImportError:
        print("❌ Production server not found")
        print("Make sure api_server_production.py exists")
    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped")

if __name__ == "__main__":
    main()
"@ | Out-File -FilePath "launch_production.py" -Encoding utf8
