from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.messages import AIMessage

from agent.graphs.base import BaseGraph

class DirectGraph(BaseGraph):
    """Single-call direct inference strategy."""

    def __init__(self, model) -> None:
        super().__init__(model)
        self.agent = create_agent(
            model=self.model,
            tools=[],
            system_prompt="You are a concise assistant. Return ONLY the final answer.",
        )

    def invoke(self, question: str) -> str:
        result = self.agent.invoke(
            {"messages": [{"role": "user", "content": question}]}
        )
        for message in reversed(result.get("messages", [])):
            if isinstance(message, AIMessage):
                return str(message.content).strip()
        return "ERROR: Invalid Response."