import re

CONTEXT_SPLIT = re.compile(
    r"answer the question using the context|"
    r"using the context provided|"
    r"based on the context above|"
    r"based on the following context",
    re.IGNORECASE,
)

MATH_LATEX: tuple[str, ...] = ("$", "\\sqrt", "\\frac", "\\boxed", "\\sum", "\\prod", "\\int")

MATH_GSM8K_VERBS = re.compile(
    r"\b(sold|bought|earn(?:ed|s)?|cost|spent|saved|split|gave|"
    r"shared|paid|owe[sd]?|borrow(?:ed|s)?|lent|charged?|"
    r"twice as|half of|each of|altogether|in total|"
    r"per (?:hour|day|week|month|year|minute|second|pound|gallon|liter|kilo))\b"
)

BOOLEAN_PREFIXES: tuple[str, ...] = (
    "is ", "are ", "can ", "could ", "would ", "should ",
    "does ", "do ", "did ", "was ", "were ", "will ",
    "has ", "have ", "had ",
)


def _question_only(question: str) -> str:
    """Strip any appended context so routing decides on the actual ask only.
    Pure local string operation — no external lookup."""
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

    if any(marker in q for marker in MATH_LATEX):
        return "math"
    if MATH_GSM8K_VERBS.search(q) and any(ch.isdigit() for ch in q):
        return "math"

    if q.lstrip().startswith(BOOLEAN_PREFIXES) and "?" in q:
        return "boolean"

    return "common_sense"
