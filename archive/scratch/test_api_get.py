import urllib.request
import json

def test_api():
    url = "http://localhost:8000/api/cameras"
    print(f"Sending GET request to {url}")
    try:
        with urllib.request.urlopen(url, timeout=3.0) as response:
            print("Status:", response.status)
            data = json.loads(response.read().decode('utf-8'))
            print("Cameras found:")
            for cam in data:
                print(f"  - ID: {cam['id']}, Name: {cam['name']}, Status: {cam['status']}, IP: {cam.get('ip') or 'N/A'}")
    except Exception as e:
        print("API Request failed:", e)

if __name__ == "__main__":
    test_api()
