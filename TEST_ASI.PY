import os
import requests

api_key = os.getenv("ASI_ONE_API_KEY")

if not api_key:
    raise ValueError("ASI API key not found!")

response = requests.post(
    "https://api.asi1.ai/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    },
    json={
        "model": "asi1",
        "messages": [
            {
                "role": "system",
                "content": "You are Scout, an AI procurement assistant for hotels."
            },
            {
                "role": "user",
                "content": "A hotel has 138 bedsheets but needs 200. Calculate the shortage."
            }
        ]
    },
    timeout=60
)

response.raise_for_status()

result = response.json()

print("\nSCOUT AI RESPONSE:\n")
print(result["choices"][0]["message"]["content"])