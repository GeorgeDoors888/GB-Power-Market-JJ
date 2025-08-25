import socket
import requests

# Test DNS resolution for NESO endpoint
try:
    print("Testing DNS resolution for data.nationalgrideso.com ...")
    ip = socket.gethostbyname("data.nationalgrideso.com")
    print(f"DNS resolved: data.nationalgrideso.com -> {ip}")
except Exception as e:
    print(f"DNS resolution failed: {e}")

# Test HTTP(S) connectivity for NESO endpoint
try:
    print("Testing HTTPS connectivity for data.nationalgrideso.com ...")
    r = requests.get("https://data.nationalgrideso.com/api/3/action/datastore_search", timeout=10)
    print(f"HTTP status: {r.status_code}")
except Exception as e:
    print(f"HTTPS connectivity failed: {e}")
