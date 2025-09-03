import os
import requests
from dotenv import load_dotenv
load_dotenv(os.path.join("../", '.env'))

API_KEY = "AIzaSyCXcVWpRaJuou-wJfHzhal3R6MTU-D7skY"

url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
headers = {
    "Content-Type": "application/json",
    "X-goog-api-key": API_KEY
}
payload = {
    "contents": [
        {
            "parts": [
                {"text": "Hello, Gemini Flash!"}
            ]
        }
    ]
}

response = requests.post(url, headers=headers, json=payload)
print("Status:", response.status_code)
print("Response:", response.json())