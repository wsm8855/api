import requests
import json

SERVER = "http://localhost:8889/"

print("Sending request...")
response = requests.get(SERVER)
print(response)

print("Sending request...")
response = requests.post(SERVER + "api/text/", data=json.dumps({"text": "echo!"}))
print(response.json())

print("Sending request...")
response = requests.post(SERVER + "api/text/", data=json.dumps({"wrong_field_name": "this should fail"}))
print(response.json())
