from langchain.tools import tool
from ddgs import DDGS
from urllib.parse import urlparse

@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
def calculator(expression: str) -> str:
    print(f"=== CALCULATOR TOOL INVOKED === \n Expression: {expression}")
    return str(eval(expression))

@tool("web_search", description="Performs a web search for the given query and returns top results.")
def web_search(query: str) -> str:
    """Performs a web search for the given query and returns top results."""
    candidates: dict[str, dict] = {}
    try:
        with DDGS() as ddgs:
            search = ddgs.text(query, max_results=5)
    except Exception:
        return "Web search failed."
    
    for r in search:
        href = r.get("href", "")
        title = r.get("title", "").strip()
        snippet = r.get("body", "").strip()
        
        if not href or not snippet:
            continue

        domain = urlparse(href).netloc
        candidates[href] = {"title": title, "snippet": snippet, "domain": domain}

    results = []
    for idx, item in enumerate(candidates.values(), start=1):
        results.append(
            f"{idx}. {item['title']}\n"
            f"Source: {item['domain']}\n"
            f"Snippet: {item['snippet']}\n"
        )

    return "\n".join(results)