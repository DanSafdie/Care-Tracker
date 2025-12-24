import os
import sys
import subprocess

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'app', 'backend'))

def run_server():
    env = os.environ.copy()
    env["PYTHONPATH"] = os.path.join(os.getcwd(), 'app', 'backend')
    try:
        # Run uvicorn directly to see output
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8005"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Read first 20 lines of output
        output = []
        for _ in range(30):
            line = process.stdout.readline()
            if not line:
                break
            output.append(line.strip())
            print(line.strip())
            if "Application startup complete" in line:
                print("SERVER STARTED SUCCESSFULLY")
                process.terminate()
                return
        
        process.terminate()
        print("\n--- END OF LOG ---")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_server()
