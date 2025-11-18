#!/usr/bin/env python3
"""
System Launcher for DocuMentor

Launches both FastAPI backend and Streamlit frontend with proper
health checking and process management.
"""

import subprocess
import sys
import time
import threading
import requests
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class ModernSystemLauncher:
    def __init__(self):
        self.fastapi_process = None
        self.streamlit_process = None
        self.api_port = 8100  # API backend
        self.ui_port = 8506   # Streamlit frontend

    def check_port_available(self, port):
        """Check if a port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return True
            except OSError:
                return False

    def wait_for_api(self, timeout=30):
        """
        Wait for FastAPI to be ready by polling the health endpoint.

        Args:
            timeout: Maximum seconds to wait for API to become ready

        Returns:
            True if API is ready, False if timeout exceeded
        """
        print(f"Waiting for FastAPI on port {self.api_port}...")

        for i in range(timeout):
            try:
                response = requests.get(f"http://127.0.0.1:{self.api_port}/", timeout=2)
                if response.status_code == 200:
                    print("FastAPI is ready")
                    return True
            except (requests.RequestException, ConnectionError, TimeoutError):
                # API not ready yet, continue polling
                pass

            time.sleep(1)
            print(f"   Attempt {i+1}/{timeout}")

        print("ERROR: FastAPI failed to start within timeout")
        return False

    def launch_fastapi(self):
        """
        Launch FastAPI backend server.

        Returns:
            True if launch successful, False otherwise
        """
        print("Starting FastAPI backend...")

        if not self.check_port_available(self.api_port):
            print(f"ERROR: Port {self.api_port} is already in use")
            return False

        try:
            self.fastapi_process = subprocess.Popen([
                sys.executable, "api_server.py",
                "--port", str(self.api_port),
                "--host", "127.0.0.1"
            ], cwd=str(project_root))

            return self.wait_for_api()
        except Exception as e:
            print(f"ERROR: Failed to start FastAPI: {e}")
            return False

    def launch_streamlit(self):
        """
        Launch Streamlit frontend server.

        Returns:
            True if launch successful, False otherwise
        """
        print("Starting Streamlit UI...")

        if not self.check_port_available(self.ui_port):
            print(f"ERROR: Port {self.ui_port} is already in use")
            return False

        try:
            self.streamlit_process = subprocess.Popen([
                sys.executable, "main.py",
                "--port", str(self.ui_port)
            ], cwd=str(project_root))

            print("Streamlit is starting...")
            return True
        except Exception as e:
            print(f"ERROR: Failed to start Streamlit: {e}")
            return False

    def show_system_info(self):
        """Display system information and access points."""
        print("=" * 70)
        print("DOCUMENTOR - AI-POWERED DOCUMENTATION ASSISTANT")
        print("=" * 70)
        print("System Features:")
        print("   - Modern UI with dark/light mode toggle")
        print("   - Multi-provider AI support (Ollama, OpenAI, etc.)")
        print("   - Technology-specific filtering (9+ frameworks)")
        print("   - Smart code generation with context")
        print("   - Intelligent documentation search")
        print("   - Real-time web search integration")
        print("   - Optimized performance and caching")
        print()
        print("Access Points:")
        print(f"   Streamlit UI:  http://127.0.0.1:{self.ui_port}")
        print(f"   FastAPI Docs: http://127.0.0.1:{self.api_port}/docs")
        print(f"   API Explorer:  http://127.0.0.1:{self.api_port}/redoc")
        print()
        print("Available Technologies:")
        technologies = [
            "Python 3.13.5", "FastAPI", "Django 5.2",
            "React & Next.js", "Node.js", "PostgreSQL",
            "MongoDB", "TypeScript", "LangChain"
        ]
        for i, tech in enumerate(technologies, 1):
            print(f"   {i:2d}. {tech}")
        print("=" * 70)

    def cleanup(self):
        """Terminate all running server processes."""
        print("\nCleaning up processes...")

        if self.fastapi_process:
            print("   Stopping FastAPI...")
            self.fastapi_process.terminate()
            try:
                self.fastapi_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.fastapi_process.kill()

        if self.streamlit_process:
            print("   Stopping Streamlit...")
            self.streamlit_process.terminate()
            try:
                self.streamlit_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.streamlit_process.kill()

        print("Cleanup complete")

    def launch_system(self):
        """
        Launch the complete system including FastAPI backend and Streamlit frontend.

        Returns:
            True if system launched and shutdown gracefully, False on error
        """
        try:
            self.show_system_info()

            # Launch FastAPI first
            if not self.launch_fastapi():
                print("ERROR: Failed to start FastAPI. Aborting launch.")
                return False

            time.sleep(2)

            # Launch Streamlit
            if not self.launch_streamlit():
                print("ERROR: Failed to start Streamlit. Stopping FastAPI.")
                self.cleanup()
                return False

            print("\nSYSTEM LAUNCHED SUCCESSFULLY!")
            print(f"Open your browser to: http://127.0.0.1:{self.ui_port}")
            print("The UI includes:")
            print("   - Modern gradient design with animations")
            print("   - Technology-specific filtering")
            print("   - Enhanced code generation mode")
            print("   - Real-time web search")
            print("   - Performance analytics")
            print("\nPress Ctrl+C to stop both services")

            # Wait for keyboard interrupt
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutdown requested...")
                self.cleanup()
                return True

        except (OSError, subprocess.SubprocessError, RuntimeError) as e:
            print(f"ERROR: Error during launch: {e}")
            self.cleanup()
            return False

def check_dependencies():
    """
    Check if required dependencies are available.

    Returns:
        True if all dependencies are available, False otherwise
    """
    print("Checking dependencies...")

    required_modules = [
        'fastapi', 'uvicorn', 'streamlit', 'requests',
        'pathlib', 'subprocess'
    ]

    missing = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        print(f"ERROR: Missing dependencies: {', '.join(missing)}")
        print("Install with: pip install fastapi uvicorn streamlit requests")
        return False

    print("All dependencies available")
    return True

def main():
    """
    Main launcher function.

    Returns:
        True if system launched successfully, False otherwise
    """
    print("DocuMentor RAG System Launcher")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        return False

    # Launch system
    launcher = ModernSystemLauncher()
    return launcher.launch_system()

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)