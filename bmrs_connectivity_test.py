import httpx

BMRS_BASE = "https://api.bmreports.com"

def test_bmrs_connect():
    try:
        resp = httpx.get(f"{BMRS_BASE}/BMRS/B0620/v1", params={"SettlementDate": "2016-01-01", "Period": 1, "ServiceType": "json"}, timeout=20)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_bmrs_connect()
