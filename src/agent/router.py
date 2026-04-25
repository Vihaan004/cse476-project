import re
def route_question(question: str) -> str:
    q = question.lower()
    
    if any(x in q for x in [
        "+", "-", "*", "/", "%", "$",
        "calculate", "solve", "find",
        "how many", "how much",
        "sum", "product", "difference", "total",
        "integer", "remainder", "probability",
        "area", "volume", "ratio",
        "\\sqrt", "\\frac", "^",
        "triangle", "circle", "quadrilateral",
    ]):
        return "math"

    if re.search(r"\([A-D]\)|\b[A-D]\.", question):
        return "mcq"

    if q.startswith(("is ", "are ", "can ", "does ", "do ", "did ", "was ", "were ")):
        return "yes_no"

    return "general"