import urllib.request
import json

def test_api():
    print("Testing local API connectivity...")
    try:
        with urllib.request.urlopen("http://localhost:8000/api/cameras", timeout=3.0) as response:
            data = json.loads(response.read().decode('utf-8'))
            print("Successfully retrieved cameras list!")
            print(f"Number of registered cameras: {len(data)}")
    except Exception as e:
        print("Failed to reach API server:", e)

if __name__ == "__main__":
    test_api()
