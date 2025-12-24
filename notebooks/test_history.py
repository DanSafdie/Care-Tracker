import requests
import subprocess
import time
import os
import sys

def test():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), 'app', 'backend')
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8009"],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    time.sleep(3)
    try:
        r = requests.get("http://127.0.0.1:8009/history")
        print(f"Status: {r.status_code}")
        if r.status_code != 200:
            print(f"Body: {r.text}")
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        process.terminate()
        stdout, stderr = process.communicate()
        print("\n--- STDERR ---")
        print(stderr)

if __name__ == "__main__":
    test()
