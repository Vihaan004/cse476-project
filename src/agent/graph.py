import re

from agent.client import call_model
from agent.normalize_answer import normalize_answer
from agent.call_counter import CallCounter
from agent.router import route_question
from agent.tools import calculator

BAD_PREFIXES = ("since", "then", "so,", "we can", "therefore", "because", "let ")

# Smaller caps = faster generation = fewer timeouts.
ROUTE_MAX_TOKENS = {
    "boolean": 8,
    "yes_no": 8,
    "math": 192,
    "common_sense": 96,
    "future_prediction": 256,
    "coding": 512,
    "planning": 1024,
    "general": 192,
    "mcq": 32,
}

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
        "Use the exact imports, function name, parameters, column names, and constants from the prompt. "
        "Return only the code that belongs after the provided starter code. "
        "Do not include markdown fences or explanation."
    ),
    "planning": (
        "Output the plan as one action per line in this exact format: (action arg1 arg2 ...).\n"
        "Examples of valid lines:\n"
        "  (feast c a)\n"
        "  (succumb c)\n"
        "  (unstack red blue)\n"
        "  (put-down red)\n"
        "  (stack blue orange)\n"
        "Use lowercase. Drop the words 'the', 'object', 'block'. "
        "Use short identifiers exactly as introduced (e.g., 'red', 'a', 'o9'). "
        "One action per line, parentheses required, no numbering, no markdown, no explanation."
    ),

    "future_prediction": (
        "Make the requested prediction. The final answer MUST end with "
        "\\boxed{...} containing a Python list literal — even single-item answers go in a list.\n"
        "Examples of valid final answers:\n"
        "  \\boxed{['No']}\n"
        "  \\boxed{[112.24]}\n"
        "  \\boxed{['item1', 'item2', 'item3']}\n"
        "String items use single quotes; numbers stay unquoted. "
        "Do not refuse, do not explain, do not output anything after the boxed line."
    ),
    "general": (
        "Think privately before answering. "
        "Do not show reasoning or explanation. "
        "Return only the final answer."
    ),
    "common_sense": (
        "Answer with the exact short factual answer only. "
        "Do not use prefixes like 'The answer is', or any explanation."
        "Return only the entity, name, place, year, or short phrase. "
        "Do not add quotes, articles you didn't see. "
        "If the question lists options, return the chosen option exactly as written. "
        "Output one line, nothing else."
    ),
    "boolean": (
        "Answer the yes/no question. "
        "Return exactly one word: True or False. "
        "Do not include reasoning, punctuation, or explanation."
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


# --- Decomposition (inference technique #8) -------------------------------
# Break a multi-step math problem into ordered sub-questions, solve each
# with prior answers as context, then combine into a final answer. Used
# when the calculator path doesn't engage. Falls back to self_consistency
# if decomposition can't produce a usable result.

_SUBQ_LINE = re.compile(r"^[\(\[]?\s*(\d+)[\.\)\]:]\s*(.+)$")


def parse_subquestions(text: str) -> list[str]:
    """Pull numbered sub-questions out of a model response."""
    if not text:
        return []
    subs: list[str] = []
    for line in (l.strip() for l in text.splitlines() if l.strip()):
        m = _SUBQ_LINE.match(line)
        if m:
            subs.append(m.group(2).strip())
    return subs[:3]


def decompose_subquestions_prompt(question: str) -> str:
    return f"""
Break this math problem into 2 or 3 ordered sub-questions. Each sub-question
should be a small concrete step that builds on the previous one.

Output exactly this format, no preamble, no explanation:
1) <sub-question>
2) <sub-question>
3) <sub-question, optional>

Problem: {question}""".strip()


def decompose_solve_prompt(
    question: str, sub: str, prior: list[tuple[str, str]]
) -> str:
    prior_block = ""
    if prior:
        bullets = "\n".join(f"- {q} -> {a}" for q, a in prior)
        prior_block = f"\nAlready solved:\n{bullets}\n"
    return f"""
Original problem (for reference): {question}{prior_block}
Now solve only this sub-question: {sub}

Return only the numeric answer or short numeric expression. No reasoning, no units.""".strip()


def decompose_combine_prompt(question: str, sub_qa: list[tuple[str, str]]) -> str:
    bullets = "\n".join(
        f"  {i + 1}. {q} -> {a}" for i, (q, a) in enumerate(sub_qa)
    )
    return f"""
Original problem: {question}

Sub-question results:
{bullets}

Using these results, give the single final numeric answer to the original problem.
Return only the number. No reasoning.""".strip()


def decompose_math(question: str, budget: CallCounter) -> str:
    """Returns the final answer or "" if decomposition can't produce one."""
    raw = budgeted_call(
        decompose_subquestions_prompt(question),
        budget,
        temperature=0.0,
        max_tokens=256,
    )
    subs = parse_subquestions(raw or "")
    if len(subs) < 2:
        return ""

    sub_qa: list[tuple[str, str]] = []
    for sub in subs:
        ans = budgeted_call(
            decompose_solve_prompt(question, sub, sub_qa),
            budget,
            temperature=0.0,
            max_tokens=128,
        )
        if ans is None:  # budget exhausted mid-decomposition
            return ""
        sub_qa.append((sub, str(ans).strip()))

    final_raw = budgeted_call(
        decompose_combine_prompt(question, sub_qa),
        budget,
        temperature=0.0,
        max_tokens=ROUTE_MAX_TOKENS.get("math", 192),
    )
    return normalize_answer(final_raw, question, "math")


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
    if route == "boolean" and low not in {"true", "false"}:
        return True
    if route == "future_prediction" and "\\boxed{" not in text:
        return True
    if route in {"coding", "planning"} and len(text) < 10:
        return True
    if route == "common_sense" and (len(text) > 200 or "\n" in text):
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
    cap = ROUTE_MAX_TOKENS.get(route, 256)
    first_raw = budgeted_call(
        hidden_cot_prompt(question, route),
        budget,
        temperature=0.0,
        max_tokens=cap,
    )
    first_answer = normalize_answer(first_raw, question, route)

    second_raw = budgeted_call(
        hidden_cot_prompt(question, route, "independent check"),
        budget,
        temperature=0.2,
        max_tokens=cap,
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
        max_tokens=ROUTE_MAX_TOKENS.get(route, 256),
    )
    return normalize_answer(raw, question, route)


def invoke_agent(question: str) -> str:
    budget = CallCounter(max_calls=20)
    route = route_question(question)

    if route == "math":
        # Path 1: tool-augmented (calculator) for simple arithmetic.
        tool_answer = tool_augmented_math(question, budget)
        if tool_answer:
            return tool_answer
        # Path 2: decomposition for multi-step problems.
        decomposed = decompose_math(question, budget)
        if decomposed and any(ch.isdigit() for ch in decomposed):
            answer = decomposed
        else:
            # Path 3: self-consistency fallback.
            answer = self_consistency(question, route, budget)

    elif route in {"coding", "planning", "future_prediction", "general", "common_sense", "boolean"}:
        answer = single_pass(question, route, budget)

    else:
        answer = self_consistency(question, route, budget)

    if is_malformed(answer, route):
        return fallback_retry(question, route, answer, budget) or answer

    return answer

