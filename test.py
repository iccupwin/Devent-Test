import requests

API_KEY = ""
url = "https://generativelanguage.googleapis.com/v1/models/gemini-1.5-pro:generateContent"
headers = {"Content-Type": "application/json"}
data = {
    "contents": [
        {"parts": [{"text": "Привет, Gemini!"}]}
    ]
}
params = {"key": API_KEY}
resp = requests.post(url, headers=headers, params=params, json=data)
print(resp.status_code, resp.text)