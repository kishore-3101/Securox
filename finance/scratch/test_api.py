import urllib.request
import json

API = "http://localhost:8000/api"

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    if data:
        req.add_header("Content-Type", "application/json")
        encoded_data = json.dumps(data).encode("utf-8")
        req.data = encoded_data
    
    try:
        with urllib.request.urlopen(req) as response:
            res_data = response.read().decode("utf-8")
            return response.status, json.loads(res_data)
    except urllib.error.HTTPError as e:
        err_data = e.read().decode("utf-8")
        return e.code, json.loads(err_data)

def test_camera_flow():
    # 1. Register Camera
    payload = {
        "name": "Intersection 8 CCTV",
        "ip": "192.168.10.15",
        "port": 8080,
        "protocol": "mjpeg",
        "username": "operator",
        "password": "secret_cctv_pass_99"
    }
    
    print("Testing Camera Registration...")
    status, response = make_request(f"{API}/cameras", method="POST", data=payload)
    print("Status Code:", status)
    print("Response JSON:", response)
    assert status == 200, "Failed to register camera"
    cam_id = response["id"]

    # 2. Get Camera Status
    print("\nTesting Get Camera Status...")
    status, response = make_request(f"{API}/cameras/{cam_id}")
    print("Status Code:", status)
    print("Response JSON:", response)
    assert status == 200, "Failed to get camera"

    # 3. Inject Anomaly
    print("\nTesting Anomaly Injection (DDoS)...")
    status, response = make_request(f"{API}/cameras/{cam_id}/anomaly", method="POST", data={"anomaly_type": "ddos", "enable": True})
    print("Status Code:", status)
    print("Response JSON:", response)
    assert status == 200, "Failed to inject ddos anomaly"

    # 4. Check stats
    print("\nChecking stats...")
    status, response = make_request(f"{API}/stats")
    print("Stats Response:", response)

    # 5. Delete Camera
    print("\nTesting Delete Camera...")
    status, response = make_request(f"{API}/cameras/{cam_id}", method="DELETE")
    print("Status Code:", status)
    print("Response JSON:", response)
    assert status == 200, "Failed to delete camera"

    print("\nAll camera registration and security lifecycle tests PASSED! 🛡️")

if __name__ == "__main__":
    test_camera_flow()
