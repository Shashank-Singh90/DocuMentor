#!/usr/bin/env python3
"""
Enhanced FastAPI v2 Startup Script
Launches the advanced REST API with all enhanced features
"""

import sys
import argparse
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_api_server(port: int = 8100, host: str = "127.0.0.1"):
    """Run the FastAPI application"""
    import uvicorn
    from rag_system.api.server import app

    print(f">> Starting DocuMentor API on {host}:{port}")
    print("API Features:")
    print("  >> Technology-specific filtering (/technologies)")
    print("  >> Advanced code generation (/generate-code/enhanced)")
    print("  >> Enhanced Q&A (/ask/enhanced)")
    print("  >> Technology-specific queries (/technology-query)")
    print("  >> Document upload and processing (/upload)")
    print(f"\n>> API Documentation: http://{host}:{port}/docs")
    print(f">> Interactive API Explorer: http://{host}:{port}/redoc")
    print("=" * 60)

    # Run FastAPI with uvicorn
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="DocuMentor API Server")
    parser.add_argument(
        "--port",
        type=int,
        default=8100,
        help="Port to run the FastAPI app on (default: 8100)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to run the FastAPI app on (default: 127.0.0.1)"
    )

    args = parser.parse_args()

    try:
        run_api_server(args.port, args.host)
    except KeyboardInterrupt:
        print("\n>> API Server stopped")
    except Exception as e:
        print(f"ERROR: Error starting API Server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()