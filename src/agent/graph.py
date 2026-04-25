from agent.client import call_model
from agent.normalize_answer import normalize_answer
from agent.call_counter import CallCounter
from agent.router import route_question
from agent.tools import calculator

BAD_PREFIXES = ("since", "then", "so,", "we can", "therefore", "because", "let ")

Arithmetic_keywords = (
    "sold", "bought", "saved", "cost", "earned", "commission",
    "percent", "week", "weeks", "pounds", "dollars", "each",
    "split", "bill", "twice", "half",
)


PROMPTS = {
    "math": (
        "Think through the solution privately. "
        "Do not write reasoning, equations, or explanation. "
        "Return only the final numeric answer."
    ),
    "mcq": (
        "Think through each option privately. "
        "Do not write reasoning or explanation. "
        "Return only the answer text."
    ),
    "yes_no": (
        "Think privately before answering. "
        "Do not write reasoning or explanation. "
        "Answer with only yes or no."
    ),
    "coding": (
        "You are an expert Python developer. "
        "Return only the requested self-contained code body. "
        "Do not include markdown, comments outside the code, or explanation."
    ),
    "planning": (
        "Generate a valid plan for the final planning problem. "
        "Return only the action list in the required parenthesized format. "
        "Do not include explanation."
    ),
    "future_prediction": (
        "Make the requested prediction. "
        "Preserve the exact required final format, especially boxed answers. "
        "Do not refuse or explain."
    ),
    "general": (
        "Think privately before answering. "
        "Do not show reasoning or explanation. "
        "Return only the final answer."
    ),
}


def hidden_cot_prompt(question: str, route: str, attempt: str = "initial") -> str:
    instruction = PROMPTS.get(route, PROMPTS["general"])
    return f"""
    {instruction}
    Attempt: {attempt}
    Question:{question}""".strip()


def budgeted_call(prompt: str, budget: CallCounter, **kwargs) -> str | None:
    if not budget.record():
        return None

    return call_model(prompt, **kwargs)


def looks_arithmetic(question: str) -> bool:
    q = question.lower()
    return any(hint in q for hint in Arithmetic_keywords) and any(ch.isdigit() for ch in q)


def expression_prompt(question: str) -> str:
    return f"""
    Convert this arithmetic word problem into one Python arithmetic expression.
    Return only the expression. Do not include words, units, or explanation.
    Question:{question}""".strip()


def tool_augmented_math(question: str, budget: CallCounter) -> str:
    if not looks_arithmetic(question):
        return ""

    raw = budgeted_call(expression_prompt(question), budget, temperature=0.0, max_tokens=96)
    expression = str(raw or "").strip().strip("`")
    if not expression:
        return ""
    expression = expression.splitlines()[-1].strip()

    try:
        return calculator(expression)
    except Exception:
        return ""


def verifier_prompt(question: str, route: str, first: str, second: str) -> str:
    instruction = PROMPTS.get(route, PROMPTS["general"])
    return f"""
    {instruction}
    Check both candidate answers against the question. 
    Choose the candidate that is more likely correct.
    Do not solve from scratch unless needed.


    Question:{question}
    Candidate A:{first}
    Candidate B:{second}""".strip()


def verify_answer(question: str, route: str, first: str, second: str, budget: CallCounter,) -> str:
    raw = budgeted_call(
        verifier_prompt(question, route, first, second),
        budget,
        temperature=0.0,
    )
    return normalize_answer(raw, question, route) or first


def retry_prompt(question: str, route: str, bad_answer: str) -> str:
    instruction = PROMPTS.get(route, PROMPTS["general"])
    return f"""
    {instruction}
    The previous answer was invalid or incomplete: {bad_answer}
    Return only the final answer in the required format.
    Do not include reasoning, equations, labels, or explanation.
    Question:{question}""".strip()


def is_malformed(answer: str, route: str) -> bool:
    text = str(answer or "").strip()
    low = text.lower()
    if not text:
        return True
    if low.startswith(BAD_PREFIXES):
        return True
    if route == "math" and not any(ch.isdigit() for ch in text):
        return True
    if route == "yes_no" and low not in {"yes", "no"}:
        return True
    if route == "future_prediction" and "\\boxed{" not in text:
        return True
    if route in {"coding", "planning"} and len(text) < 10:
        return True
    return False


def fallback_retry(question: str, route: str, bad_answer: str, budget: CallCounter) -> str:
    raw = budgeted_call(
        retry_prompt(question, route, bad_answer),
        budget,
        temperature=0.0,
    )
    return normalize_answer(raw, question, route)


def self_consistency(question: str, route: str, budget: CallCounter) -> str:
    first_raw = budgeted_call(
        hidden_cot_prompt(question, route),
        budget,
        temperature=0.0,
    )
    first_answer = normalize_answer(first_raw, question, route)

    second_raw = budgeted_call(
        hidden_cot_prompt(question, route, "independent check"),
        budget,
        temperature=0.2,
    )
    second_answer = normalize_answer(second_raw, question, route)

    if first_answer and first_answer == second_answer:
        return first_answer
    
    if first_answer and second_answer:
        return verify_answer(question, route, first_answer, second_answer, budget)

    return first_answer or second_answer

def single_pass(question: str, route: str, budget: CallCounter) -> str:
    raw = budgeted_call(
        hidden_cot_prompt(question, route),
        budget,
        temperature=0.0,
    )
    return normalize_answer(raw, question, route)


def invoke_agent(question: str) -> str:
    budget = CallCounter(max_calls=20)
    route = route_question(question)

    if route == "math":
        tool_answer = tool_augmented_math(question, budget)
        if tool_answer:
            return tool_answer
        answer = self_consistency(question, route, budget)

    elif route in {"coding", "planning", "future_prediction"}:
        answer = single_pass(question, route, budget)

    else:
        answer = self_consistency(question, route, budget)

    if is_malformed(answer, route):
        return fallback_retry(question, route, answer, budget) or answer

    return answer

