import re

def route_question(question: str) -> str:
    q = question.lower()

    if "you should write self-contained code" in q or "def task_func" in q:
        return "coding"

    if "[plan]" in q or "my plan is as follows" in q:
        return "planning"

    if "predict future events" in q or "\\boxed" in q:
        return "future_prediction"

    if re.search(r"\([A-D]\)|\b[A-D]\.", question):
        return "mcq"

    if q.startswith(("is ", "are ", "can ", "does ", "do ", "did ", "was ", "were ")):
        return "yes_no"

    if any(x in q for x in [
        "$", "calculate", "solve", "find", "how many", "how much",
        "sum", "product", "difference", "total", "integer",
        "remainder", "probability", "area", "volume", "ratio",
        "\\sqrt", "\\frac", "triangle", "circle", "quadrilateral",
    ]):
        return "math"

    return "general"
