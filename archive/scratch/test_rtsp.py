import sys
import os
import json
import cv2
from cryptography.fernet import Fernet

CAMERAS_FILE = "backend/database/cameras.json"
KEY_FILE = "backend/database/camera_key.key"

def decrypt_password(encrypted_pw):
    with open(KEY_FILE, "rb") as f:
        key = f.read()
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_pw.encode()).decode()

def test_cameras():
    if not os.path.exists(CAMERAS_FILE):
        print(f"File {CAMERAS_FILE} does not exist.")
        return

    with open(CAMERAS_FILE, "r") as f:
        cameras = json.load(f)
    
    for cam_id, cam in cameras.items():
        if cam_id == "CAM_TRAFFIC_01":
            continue
            
        print(f"\n=========================================")
        print(f"Testing Camera: {cam.get('name')} ({cam_id})")
        print(f"IP/Port: {cam.get('ip')}:{cam.get('port')}")
        print(f"Brand: {cam.get('brand', 'generic')}")
        print(f"Connection Type: {cam.get('connection_type', 'ip')}")
        
        if cam.get('connection_type') == 'p2p':
            print(f"Serial/UID: {cam.get('serial_number')}")
            print("P2P cameras do not have direct IP/RTSP streams on the local network without a P2P cloud relay.")
            continue
            
        if not cam.get('ip'):
            print("No IP address configured.")
            continue
            
        try:
            password = decrypt_password(cam['encrypted_password'])
            username = cam['username']
            ip = cam['ip']
            port = cam['port']
            brand = cam.get('brand', 'generic').lower()
            
            print(f"Username: {username}")
            print(f"Password: {password}")
            
            paths = {
                "tapo": ["/stream1", "/stream2"],
                "hikvision": ["/Streaming/Channels/101", "/Streaming/Channels/102"],
                "dahua": ["/cam/realmonitor?channel=1&subtype=0"],
                "reolink": ["/h264Preview_01_main"],
                "generic": ["/stream1", "/stream2", "/live/ch0", "/videoMain", ""]
            }.get(brand, ["/stream1", "/stream2", ""])
            
            for path in paths:
                rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{path}"
                print(f"Trying: {rtsp_url.replace(password, '****')}")
                cap = cv2.VideoCapture(rtsp_url)
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret:
                        print(f"  SUCCESS on path {path}! Frame shape: {frame.shape}")
                        cap.release()
                        break
                    else:
                        print(f"  Opened but failed to read frame on path {path}")
                else:
                    print(f"  Failed to open connection on path {path}")
                cap.release()
        except Exception as e:
            print(f"Error testing camera: {e}")

if __name__ == "__main__":
    test_cameras()
