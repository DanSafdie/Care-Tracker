#!/usr/bin/env python3
"""
Convenience script to run the Pet Care Tracker server.
Usage: python run.py [--host HOST] [--port PORT]
"""
import sys
import os

# Add the backend directory to the path so imports work correctly
backend_path = os.path.join(os.path.dirname(__file__), 'app', 'backend')
sys.path.insert(0, backend_path)

if __name__ == "__main__":
    import uvicorn
    
    # Default settings - bind to all interfaces for LAN access
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "8000"))
    
    print(f"Starting Pet Care Tracker on http://{host}:{port}")
    print("Access from other devices on your network using your machine's IP address")
    print("Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True,
        reload_dirs=[backend_path]
    )
