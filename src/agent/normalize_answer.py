import re

NUMBERS = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")
PREFIX = re.compile(r"^\s*(?:final answer|answer|the answer is|therefore|thus|result|hence)\s*[:\-]?\s*", re.IGNORECASE)

def normalize_answer(answer: str, question: str = "", route: str = "general") -> str:
    text = str(answer or "").strip()

    if route == "coding":
        text = re.sub(r"^```(?:python)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    if route == "planning":
        text = re.sub(r"^```(?:text)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    if route == "future_prediction":
        boxed = re.search(r"\\boxed\{.*?\}", text)
        if boxed:
            return boxed.group(0)
        return text.strip()

    # only short-answer routes use last-line cleanup
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

    if route == "common_sense":
        return text.strip(" .\"'`")
    if route == "boolean":
        low = text.lower()
        if "true" in low or low.startswith("yes"):
            return "True"
        if "false" in low or low.startswith("no"):
            return "False"
        return text.strip(" .")

    return text.strip(" .")
