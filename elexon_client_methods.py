from ElexonDataPortal import api

api_key = "DUMMY_API_KEY"
client = api.Client(api_key)

print("client.methods:", getattr(client, "methods", None))
