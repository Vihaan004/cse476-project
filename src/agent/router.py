import re
def route_question(question: str) -> str:
    q = question.lower()

    if any(x in q for x in ["+", "-", "*", "/", "%", "calculate", "solve"]):
        return "math"

    if re.search(r"\([A-D]\)", question):
        return "mcq"

    if q.startswith(("is ", "are ", "can ", "does ", "do ")):
        return "yes_no"

    return "general"