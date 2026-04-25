import os

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
API_BASE = os.getenv("API_BASE", "https://openai.rc.asu.edu/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-30b-a3b-instruct-2507")


def call_model(
    prompt: str,
    system: str = "You are a precise problem solver.",
    temperature: float = 0.0,
) -> str:
    if not API_KEY:
        raise RuntimeError("Missing API key. Set OPENAI_API_KEY or LLM_API_KEY.")

    url = f"{API_BASE}/chat/completions"

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code != 200:
        raise RuntimeError(f"API error {response.status_code}: {response.text}")

    data = response.json()
    return data["choices"][0]["message"]["content"].strip()
