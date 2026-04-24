import re

NUMBERS = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
PREFIX = re.compile(r"^\s*(?:final answer|answer|the answer is|therefore|thus|result|hence)\s*[:\-]?\s*", re.IGNORECASE)

def normalize_answer(answer: str, question: str = "") -> str:
    text = str(answer or "").strip()

    # use last line if model included reasoning
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if lines:
        text = lines[-1]

    # remove common prefixes
    text = PREFIX.sub("", text).strip()
    text = text.strip("`'\" $.")

    # if line has math explanantion like a + b = 25 then just return the final number
    numbers = NUMBERS.findall(text)
    if numbers:
        return numbers[-1].replace(",", "")

    return text.strip(" .")