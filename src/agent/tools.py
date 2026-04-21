from langchain.tools import tool

@tool("calculator", description="Performs arithmetic calculations. Use this for any math problems.")
def calculator(expression: str) -> str:
    print(f"=== CALCULATOR TOOL INVOKED === \n Expression: {expression}")
    return str(eval(expression))

# @tool
# def google_search(query: str) -> str:
#     return result