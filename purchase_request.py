import os
import json
import requests

ASI_API_KEY = os.environ.get("ASI_ONE_API_KEY")


def extract_purchase_request(user_message):

    if not ASI_API_KEY:
        raise ValueError("ASI_ONE_API_KEY is missing")

    response = requests.post(
        "https://api.asi1.ai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {ASI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "asi1",
            "messages": [
                {
                    "role": "system",
                    "content": """
Extract purchase details from the user's message.

Return ONLY valid JSON:
{
    "product": "product name or null",
    "quantity": number or null,
    "delivery_location": "location or null",
    "delivery_days": number or null
}

Never invent missing information.
"""
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
        },
        timeout=60
    )

    response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"]

    content = content.strip()

    if content.startswith("```"):
        content = content.split("\n", 1)[1]
        content = content.rsplit("```", 1)[0].strip()

    return json.loads(content)