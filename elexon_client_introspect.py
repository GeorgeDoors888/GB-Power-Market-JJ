from ElexonDataPortal import api

api_key = "DUMMY_API_KEY"
client = api.Client(api_key)

print("dir(client):", dir(client))
print("client.__doc__:", client.__doc__)
print("api.__doc__:", api.__doc__)
print("dir(api):", dir(api))
