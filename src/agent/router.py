from __future__ import annotations

from agent.client import get_model
from agent.graphs.base import BaseGraph
from agent.graphs.direct import DirectGraph


def _build_registry() -> dict[str, BaseGraph]:
    """Create strategy instances once so model/agent setup is reused."""
    model = get_model()
    return {
        "direct": DirectGraph(model),
    }


REGISTRY = _build_registry()


def list_strategies() -> list[str]:
    return sorted(REGISTRY.keys())


def invoke_agent(question: str, strategy: str = "direct") -> str:
    if strategy not in REGISTRY:
        available = ", ".join(list_strategies())
        raise ValueError(f"Unknown strategy '{strategy}'. Available: {available}")
    return REGISTRY[strategy].invoke(question)
