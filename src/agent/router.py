import re

CONTEXT_SPLIT = re.compile(
    r"answer the question using the context|"
    r"using the context provided|"
    r"based on the context above|"
    r"based on the following context",
    re.IGNORECASE,
)


def _question_only(question: str) -> str:
    """Strip any appended Wikipedia/HotpotQA context so routing decides on the
    actual ask, not on stray math symbols sitting in the passage."""
    return CONTEXT_SPLIT.split(question, maxsplit=1)[0]


def route_question(question: str) -> str:
    routing_text = _question_only(question)
    q = routing_text.lower()

    if "you should write self-contained code" in q or "def task_func" in q:
        return "coding"

    if "[plan]" in q or "my plan is as follows" in q:
        return "planning"

    if "predict future events" in q or "\\boxed" in q:
        return "future_prediction"

    if re.search(r"\([A-D]\)|\b[A-D]\.", routing_text):
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

    return "common_sense"
