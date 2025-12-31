#!/usr/bin/env python3
"""
Convenience script to run the Care-Tracker server.
Usage: python run.py [--host HOST] [--port PORT]
"""
import sys
import os

# Add the backend directory to the path so imports work correctly
backend_path = os.path.join(os.path.dirname(__file__), 'app', 'backend')
sys.path.insert(0, backend_path)

if __name__ == "__main__":
    import uvicorn
    import argparse
    import subprocess
    
    parser = argparse.ArgumentParser(description="Run Care-Tracker server or tests.")
    parser.add_argument("--test", action="store_true", help="Run the test suite")
    parser.add_argument("--host", default=os.environ.get("HOST", "0.0.0.0"), help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8273")), help="Port to bind to")
    
    args = parser.parse_args()

    if args.test:
        print("Running test suite...")
        # Use the current python interpreter to run pytest
        result = subprocess.call([sys.executable, "-m", "pytest"])
        sys.exit(result)
    
    print(f"Starting Care-Tracker on http://{args.host}:{args.port}")
    print("Access from other devices on your network using your machine's IP address")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=True,
        reload_dirs=[backend_path]
    )
