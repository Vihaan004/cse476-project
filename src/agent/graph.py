from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.messages import AIMessage
from agent.tools import calculator


ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

def _env(name: str, *aliases: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    for alias in aliases:
        value = os.getenv(alias)
        if value:
            return value
    return default

def invoke_agent(question: str) -> str:
    client = ChatOpenAI(
        base_url=_env("API_BASE", "BASE_URL", default="https://openai.rc.asu.edu/v1"),
        api_key=_env("OPENAI_API_KEY", "LLM_API_KEY"),
        model=_env("MODEL_NAME", default="qwen3-30b-a3b-instruct-2507"),
        temperature=float(_env("TEMPERATURE", default="0.4")),
    )

    agent = create_agent(
        model=client,
        tools=[calculator],
        system_prompt="You are a concise assistant. Return ONLY the final answer.",
    )

    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]}
    )
    
    print(f"=== API RESPONSE === \n {result}")  # debug
    for message in reversed(result.get("messages", [])):
        if isinstance(message, AIMessage):
            return str(message.content).strip()
    return "ERROR: Invalid Response."