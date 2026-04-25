import re

NUMBERS = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
PREFIX = re.compile(
    r"^\s*(?:final answer|answer|the answer is|therefore|thus|result|hence)\s*[:\-]?\s*",
    re.IGNORECASE,
)

def normalize_answer(answer: str, question: str = "", route: str = "general") -> str:
    text = str(answer or "").strip()

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        text = lines[-1]

    text = PREFIX.sub("", text).strip()
    text = text.strip("`'\" $.")

    if route == "math":
        numbers = NUMBERS.findall(text)
        if numbers:
            return numbers[-1].replace(",", "")
        return text.strip(" .")

    if route == "yes_no":
        low = text.lower()
        if "yes" in low:
            return "yes"
        if "no" in low:
            return "no"
        return text.strip(" .")

    if route == "mcq":
        m = re.search(r"\b([A-D])\b", text)
        if m:
            return m.group(1)
        return text.strip(" .")

    return text.strip(" .")