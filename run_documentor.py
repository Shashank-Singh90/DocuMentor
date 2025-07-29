import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def run_streamlit():
    """Start Streamlit interface"""
    print("🚀 Starting DocuMentor Streamlit interface...")
    subprocess.Popen([sys.executable, "-m", "streamlit", "run", "app.py"])
    time.sleep(3)
    webbrowser.open("http://localhost:8501")
    print("✅ DocuMentor Streamlit ready at: http://localhost:8501")

def run_api():
    """Start API server"""
    print("🔌 Starting DocuMentor API server...")
    subprocess.Popen([sys.executable, "api_server.py"])
    time.sleep(3)
    webbrowser.open("http://localhost:8000/docs")
    print("✅ DocuMentor API ready at: http://localhost:8000")

def run_both():
    """Start both Streamlit and API"""
    print("🎯 Starting complete DocuMentor system...")
    run_streamlit()
    time.sleep(2)
    run_api()
    print("🎉 DocuMentor complete system is running!")

def add_new_docs():
    """Add new documentation sources"""
    print("📚 Choose documentation to scrape:")
    print("1. Node.js")
    print("2. Vue.js") 
    print("3. Angular")
    print("4. Custom URL")
    
    choice = input("Enter choice (1-4): ")
    # Implementation for new scrapers

if __name__ == "__main__":
    print("🧠 DocuMentor Control Center")
    print("=" * 40)
    print("1. Start Streamlit Interface")
    print("2. Start API Server")
    print("3. Start Both (Complete System)")
    print("4. Add New Documentation")
    print("5. View Statistics")
    print("6. Deploy to Cloud")
    
    choice = input("\nSelect option (1-6): ")
    
    if choice == "1":
        run_streamlit()
    elif choice == "2":
        run_api()
    elif choice == "3":
        run_both()
    elif choice == "4":
        add_new_docs()
    else:
        print("Invalid choice")