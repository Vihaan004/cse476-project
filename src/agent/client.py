import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(override=True)

BACKEND = os.getenv("BACKEND")
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
API_BASE = os.getenv("API_BASE", "https://openai.rc.asu.edu/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "qwen3-30b-a3b-instruct-2507")
RETRY_DELAY = 10
MAX_RETRIES = 3

def _call_model_ollama(
    prompt: str,
    system: str = "You are a precise problem solver.",
    temperature: float = 0.0,
    timeout: int = 180,
) -> str:
    if not API_BASE:
        raise RuntimeError("Missing API base URL. Set API_BASE. Check ollama serve process.")

    url = f"{API_BASE}/chat/completions"

    headers = {
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

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    return response


def _call_model_cloud(
    prompt: str,
    system: str = "You are a precise problem solver.",
    temperature: float = 0.0,
    timeout: int = 60,
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

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    return response


def call_model(
    prompt: str,
    system: str = "You are a precise problem solver.",
    temperature: float = 0.0,
    timeout: int = 60,
) -> str:
    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            if BACKEND == "ollama":
                response = _call_model_ollama(prompt, system, temperature)
            else:
                response = _call_model_cloud(prompt, system, temperature, timeout)
                
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()
                return content
            
            error = RuntimeError(f"API error {response.status_code}: {response.text}")
            if response.status_code not in (500, 502, 503, 504):
                raise error
            print(f"Retryable error (attempt {attempt + 1}): {error}", flush=True)

        except requests.RequestException as e:
            print(f"Request error (attempt {attempt + 1}): {e}", flush=True)

        attempt += 1
        time.sleep(RETRY_DELAY)
    

