import socket
import urllib.request
import urllib.error

def test_port(ip, port):
    try:
        with socket.create_connection((ip, port), timeout=2.0):
            print(f"Port {port} is OPEN on {ip}")
            return True
    except Exception as e:
        print(f"Port {port} is CLOSED on {ip}: {e}")
        return False

ip = "192.168.0.8"
for port in [80, 554, 8554, 8000, 8080]:
    test_port(ip, port)
