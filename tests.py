import requests
import json

SERVER = "http://localhost:8889/"

print("Sending request...")
response = requests.get(SERVER)
print(response)

# print("Sending text request (good)...")
# response = requests.post(SERVER + "api/text/", data=json.dumps({"text": "echo!"}))
# print(response.json())
#
# print("Sending text request (bad)...")
# response = requests.post(SERVER + "api/text/", data=json.dumps({"wrong_field_name": "this should fail"}))
# print(response.json())

print("Sending categorical query (good)")
response = requests.post(SERVER + "api/categoricalQuery/",
                         data=json.dumps({
                             "age": [24, 26],
                             "ethnicities": ["Caucasian"],
                             "genders": ["Female"],
                             "states": ["New york"],
                         }))
print(response.json())

print("Sending recommendation query (good)")
response = requests.post(SERVER + "api/text/",
                         data=json.dumps({
                             "text": None,
                             "questionUno": "9AA6F105-BE5F-4A9A-876A-B118236151FC"
                         }))
print(response.json())

print("Sending recommendation query (bad)")
response = requests.post(SERVER + "api/text/",
                         data=json.dumps({
                             "text": None,
                             "questionUno": None
                         }))
print(response.json())
