import requests
import json
from server.config import settings

def test_api():
    url = f"{settings.openai_base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": settings.openai_model,
        "messages": [
            {"role": "user", "content": "Hello, are you there?"}
        ],
        "temperature": 0.7
    }
    
    print(f"Testing API: {url}")
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()