import subprocess
import time
import requests
import os
import sys

def test():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), 'app', 'backend')
    
    # Start server on a fresh port
    port = 8011
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    print(f"Waiting for server on port {port}...")
    time.sleep(5)
    
    try:
        print("Making request to / ...")
        r = requests.get(f"http://127.0.0.1:{port}/")
        print(f"Home Status: {r.status_code}")
        if r.status_code == 500:
            print("!!! HOME PAGE 500 ERROR !!!")
            
        print("\nMaking request to /history ...")
        r = requests.get(f"http://127.0.0.1:{port}/history")
        print(f"History Status: {r.status_code}")
        if r.status_code == 500:
            print("!!! HISTORY PAGE 500 ERROR !!!")
            
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        print("\nStopping server...")
        process.terminate()
        stdout, stderr = process.communicate()
        print("\n--- SERVER STDERR ---")
        print(stderr)
        print("\n--- SERVER STDOUT ---")
        print(stdout)

if __name__ == "__main__":
    test()
