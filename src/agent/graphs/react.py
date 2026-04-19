from __future__ import annotations

from agent.graphs.base import BaseGraph


class ReactGraph(BaseGraph):
	"""Placeholder for ReAct strategy implementation."""

	def invoke(self, question: str) -> str:
		raise NotImplementedError("ReactGraph is not implemented yet.")

