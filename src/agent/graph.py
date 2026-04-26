from __future__ import annotations

import argparse
import os
from pathlib import Path
from pyexpat.errors import messages
from typing import List, Literal
from typing_extensions import TypedDict, Annotated
import operator

from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from agent.tools import calculator, web_search
_tools = [calculator, web_search]

# ==================== setup environment and model ====================
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

model = ChatOpenAI(
    base_url=_env("BASE_URL", default="https://openai.rc.asu.edu/v1"),
    api_key=_env("OPENAI_API_KEY", "LLM_API_KEY"),
    model=_env("MODEL_NAME", default="qwen3-30b-a3b-instruct-2507"),
)
model_with_tools = model.bind_tools(_tools)


# ==================== define state and nodes ====================
class AgentState(TypedDict):
    messages: Annotated[List[AnyMessage], operator.add]
    llm_calls: int

def llm_node(state: AgentState) -> AgentState:
    return {"messages": [model_with_tools.invoke([SystemMessage(
        content="You are a concise assistant. Return ONLY the final answer."
        )]
        + state["messages"]
        )],
        "llm_calls": state.get("llm_calls", 0) + 1,
    }


# ==================== conditional routing ====================
# ignore static type error for END
def route_after_llm(state: AgentState) -> Literal["tool_node", END]: 
    if state["messages"][-1].tool_calls:
        return "tool_node"
    return END


# ==================== create graph ====================
def create_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # add nodes
    graph.add_node("llm_node", llm_node)
    graph.add_node("tool_node", ToolNode(_tools))

    # add edges
    graph.add_edge(START, "llm_node")
    graph.add_conditional_edges(
        "llm_node",
        route_after_llm,
        ["tool_node", END]
    )
    graph.add_edge("tool_node", "llm_node")

    return graph.compile()


# ==================== invoke agent ====================
def invoke_agent(question: str) -> str:
    agent = create_graph()

    # save graph visualization
    image_data = agent.get_graph(xray=True).draw_mermaid_png()
    with open("agent_graph.png", "wb") as f:
        f.write(image_data)
    
    messages = [HumanMessage(content=question)]
    messages = agent.invoke({"messages": messages})
    final_message = messages["messages"][-1].content

    # debug
    # print(messages)
    for m in messages["messages"]:
        m.pretty_print()

    return final_message


def main():
    parser = argparse.ArgumentParser(description="Invoke the agent with a question.")
    parser.add_argument(
        "-q",
        "--question",
        default="Who are you and what can you do?",
        help="Question prompt sent to the agent.",
    )
    args = parser.parse_args()
    invoke_agent(args.question)

if __name__ == "__main__":
    main()
