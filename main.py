#!/usr/bin/env python3
"""
DocuMentor - Main Entry Point
"""

import sys
import argparse
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def start_web_interface(port: int = 8506):
    """Start the web interface using Streamlit"""
    import streamlit.web.cli as stcli

    # Path to the web app
    app_path = project_root / "rag_system" / "web" / "app.py"

    # Streamlit arguments
    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.port", str(port),
        "--server.address", "127.0.0.1",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--theme.base", "light"
    ]

    # Run Streamlit
    stcli.main()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DocuMentor - AI Documentation Assistant")
    parser.add_argument(
        "--port",
        type=int,
        default=8506,
        help="Port to run the Streamlit app on (default: 8506)"
    )

    args = parser.parse_args()

    print(f">> Starting DocuMentor on port {args.port}")
    print("Features:")
    print("  >> Documentation search and analysis")
    print("  >> Code generation with context")
    print("  >> Technology-specific filtering")
    print("  >> Web search integration")
    print("  >> Multi-provider AI support (Ollama, OpenAI, Gemini)")
    print(f"\n>> Open your browser to: http://127.0.0.1:{args.port}")
    print("=" * 60)

    try:
        start_web_interface(args.port)
    except KeyboardInterrupt:
        print("\n>> DocuMentor stopped")
    except Exception as e:
        print(f"ERROR: Error starting DocuMentor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()