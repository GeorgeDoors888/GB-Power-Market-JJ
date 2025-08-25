from ElexonDataPortal import api

api_key = "DUMMY_API_KEY"
client = api.Client(api_key)

# Try calling one of the methods with minimal args to see the signature
import inspect
for method_name in list(client.methods.keys())[:3]:
    method = getattr(client, method_name)
    print(f"Signature for {method_name}: {inspect.signature(method)}")
    print(f"Doc for {method_name}: {method.__doc__}")
