import urllib.request
import ssl

def test_http():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    # Try HTTPS first since it threw SSL alert handshake failure
    url = "https://192.168.1.108:80/"
    print(f"Sending HTTPS GET to: {url} (bypassing SSL verification)")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3.0, context=ctx) as response:
            print("Status Code:", response.status)
            print("Headers:")
            for k, v in response.getheaders():
                print(f"  {k}: {v}")
            body = response.read(1000).decode('utf-8', errors='ignore')
            print("\nBody snippet:")
            print(body[:300])
            return
    except Exception as e:
        print("HTTPS Error:", e)
        
    # Try HTTP as fallback
    url2 = "http://192.168.1.108:80/"
    print(f"Sending HTTP GET to: {url2}")
    try:
        req = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3.0) as response:
            print("Status Code:", response.status)
            print("Headers:")
            for k, v in response.getheaders():
                print(f"  {k}: {v}")
    except Exception as e:
        print("HTTP Error:", e)

if __name__ == "__main__":
    test_http()
