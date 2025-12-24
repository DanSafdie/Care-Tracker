from fastapi.testclient import TestClient
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'app', 'backend'))

from main import app

client = TestClient(app)

def test_home():
    try:
        response = client.get("/")
        print(f"Status: {response.status_code}")
        if response.status_code != 200:
            print(f"Content: {response.text}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_home()
