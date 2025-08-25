from ElexonDataPortal import api

# Test API client instantiation (no API key needed for this import test)
try:
    client = api.Client("DUMMY_API_KEY")
    print("ElexonDataPortal import and client creation: SUCCESS")
except Exception as e:
    print(f"ElexonDataPortal import or client creation: FAILED - {e}")
