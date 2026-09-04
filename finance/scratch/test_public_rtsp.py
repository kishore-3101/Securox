import cv2

def test_public():
    url = "rtsp://rtsp.stream/pattern"
    print(f"Testing public RTSP stream: {url}")
    cap = cv2.VideoCapture(url)
    if not cap.isOpened():
        print("Could not open public stream.")
        return
        
    ret, frame = cap.read()
    if ret:
        print(f"Success! Read frame of size: {frame.shape}")
    else:
        print("Failed to read frame.")
    cap.release()

if __name__ == "__main__":
    test_public()
