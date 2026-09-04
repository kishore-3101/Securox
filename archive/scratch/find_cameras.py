import socket
import threading
from concurrent.futures import ThreadPoolExecutor

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.254.254.254', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def check_ip_port(ip, port, timeout=0.3):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            print(f"Found active port {port} on {ip}")
            return ip, port
    except Exception:
        return None

def scan_network():
    local_ip = get_local_ip()
    print(f"Local IP: {local_ip}")
    if local_ip == '127.0.0.1':
        print("Not connected to a network, scanning 192.168.1.X subnet as fallback")
        base = "192.168.1"
    else:
        parts = local_ip.split('.')
        base = ".".join(parts[:3])
    
    print(f"Scanning subnet: {base}.0/24")
    
    ports = [80, 554, 8899, 8554]
    ips = [f"{base}.{i}" for i in range(1, 255)]
    
    found = []
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for ip in ips:
            for port in ports:
                futures.append(executor.submit(check_ip_port, ip, port))
        
        for future in futures:
            res = future.result()
            if res:
                found.append(res)
    
    print("\nScan complete. Found cameras/services:")
    for ip, port in found:
        print(f"  {ip}:{port}")

if __name__ == "__main__":
    scan_network()
