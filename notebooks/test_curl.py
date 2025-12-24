import subprocess
import time
import os
import sys

def test():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), 'app', 'backend')
    
    # Start server
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8008"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    time.sleep(3) # Wait for startup
    
    try:
        import requests
        r = requests.get("http://127.0.0.1:8008/")
        print(f"Status: {r.status_code}")
        print(f"Body snippet: {r.text[:500]}")
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        process.terminate()
        stdout, stderr = process.communicate()
        print("\n--- STDOUT ---")
        print(stdout)
        print("\n--- STDERR ---")
        print(stderr)

if __name__ == "__main__":
    test()
