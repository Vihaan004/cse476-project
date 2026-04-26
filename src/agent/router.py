import re

CONTEXT_SPLIT = re.compile(
    r"answer the question using the context|"
    r"using the context provided|"
    r"based on the context above|"
    r"based on the following context",
    re.IGNORECASE,
)

MATH_LATEX: tuple[str, ...] = ("$", "\\sqrt", "\\frac", "\\boxed", "\\sum", "\\prod", "\\int")

# Step 6: targeted math phrasing to recover word problems that have neither
# LaTeX nor a GSM8K verb (e.g., "What is the smallest perfect cube...",
# "Expand and simplify...", "Calculate the greatest common factor of...").
MATH_PHRASES: tuple[str, ...] = (
    "polynomial",
    "modulo",
    "divisible by",
    "remainder when",
    "real roots",
    "real solution",
    "smallest positive integer",
    "largest positive integer",
    "least positive",
    "find the area",
    "find the volume",
    "find the value of",
    "find the number of",
    "find the sum of",
    "find the product of",
    "probability that",
    "probability of",
    "express your answer",
    "common fraction",
    "simplest form",
    "lowest terms",
    "scientific notation",
    "decimal places",
    "perfect cube",
    "perfect square",
    "greatest common factor",
    "least common multiple",
    "minimum number of",
    "maximum number of",
    "what percentage",
    "what fraction",
    "what is the perimeter",
    "what is the length",
    "what is the result",
    "expand and simplify",
    "calculate the",
    "compute the",
    "evaluate the",
    "determine the value",
)

MATH_GSM8K_VERBS = re.compile(
    r"\b(sold|bought|earn(?:ed|s)?|cost(?:s)?|spent|saved|"
    r"split|shared|paid|owe[sd]?|borrow(?:ed|s)?|lent|charged?|"
    r"twice as|half of|each of|altogether|in total|"
    r"per (?:hour|day|week|month|year|minute|second|pound|gallon|liter|kilo))\b"
)

# "How many" and "how much" are reliable math signals; broader variants
# (how long/old/far/tall) leak common_sense, so we keep them out.
MATH_HOW = re.compile(r"\bhow (?:many|much)\b")

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
    if any(phrase in q for phrase in MATH_PHRASES):
        return "math"
    if MATH_HOW.search(q):
        return "math"
    if MATH_GSM8K_VERBS.search(q) and any(ch.isdigit() for ch in q):
        return "math"

    if q.lstrip().startswith(BOOLEAN_PREFIXES) and "?" in q:
        return "boolean"

    return "common_sense"
