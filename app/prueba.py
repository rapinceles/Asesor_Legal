#!bin/python3

import requests

url = "http://localhost:8000/api/v1/agentes/1"

response = requests.get(url)

print(response.json())