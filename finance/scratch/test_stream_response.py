import urllib.request
import re

def test_stream():
    url = "http://localhost:8000/api/cameras/CAM_6E62783B/stream"
    print(f"Requesting stream: {url}")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5.0) as response:
            print("Status:", response.status)
            print("Headers:")
            for k, v in response.getheaders():
                print(f"  {k}: {v}")
                
            # Read first 100KB which should contain the first multipart boundary and frame
            data = response.read(100000)
            print(f"Read {len(data)} bytes of stream data.")
            
            # Find the JPEG start marker 0xff 0xd8 and end marker 0xff 0xd9
            start = data.find(b'\xff\xd8')
            end = data.find(b'\xff\xd9', start)
            
            if start != -1 and end != -1:
                jpeg_bytes = data[start:end+2]
                out_path = "scratch/test_stream_frame.jpg"
                with open(out_path, "wb") as f:
                    f.write(jpeg_bytes)
                print(f"Saved extracted frame to {out_path}")
            else:
                print("Could not find JPEG start/end in stream chunk.")
    except Exception as e:
        print("Stream Request failed:", e)

if __name__ == "__main__":
    test_stream()
