from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseGraph(ABC):
    """Shared interface for all inference strategies under graphs/."""

    def __init__(self, model: Any) -> None:
        self.model = model

    @abstractmethod
    def invoke(self, question: str) -> str:
        """Run the strategy and return the final answer string."""
        raise NotImplementedError
