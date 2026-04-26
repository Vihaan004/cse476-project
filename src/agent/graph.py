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
        "Solve the problem carefully. "
        "You may use reasoning and equations in your response. "
        "End with exactly one line: Final answer: <answer>."
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
        "Return only the final plan. "
        "Use one action per line. "
        "Every action must be wrapped in parentheses. "
        "Use compact symbolic action syntax from the prompt, not natural language. "
        "Use hyphenated action names where shown, like pick-up, put-down, load-truck, and fly-airplane. "
        "Abbreviate objects exactly as in examples: package_2 as p2, truck_0 as t0, airplane_1 as a1, "
        "location_0_1 as l0-1, city_2 as c2, object_9 as o9, and object a as a. "
        "Do not include [PLAN], [PLAN END], explanation, numbering, bullets, or markdown. "
        "Example output line: (unstack blue yellow)"
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


def decomposition_prompt(question: str) -> str:
    return f"""
    Decompose this math problem privately into the needed smaller facts.
    Solve each part privately and combine them.
    Do not show the decomposition, reasoning, equations, labels, or explanation.
    Return only the final numeric answer.
    Question:{question}""".strip()


def tree_of_thought_prompt(question: str) -> str:
    return f"""
    Explore three private solution approaches for this math problem:
    algebraic, structural/geometric, and casework/counting.
    Compare the approaches privately and keep the most consistent result.
    Do not show any reasoning, equations, labels, or explanation.
    Return only the final numeric answer.
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

    raw = budgeted_call(expression_prompt(question), budget, temperature=0.0)
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


def verify_candidates(question: str, route: str, candidates: list[str], budget: CallCounter) -> str:
    candidate_text = "\n".join(
        f"Candidate {idx + 1}: {candidate}" for idx, candidate in enumerate(candidates)
    )
    raw = budgeted_call(
        f"""
        {PROMPTS.get(route, PROMPTS["general"])}
        Choose the most likely correct candidate answer.
        Return only the selected final answer.
        Question:{question}
        {candidate_text}""".strip(),
        budget,
        temperature=0.0,
    )
    return normalize_answer(raw, question, route) or candidates[0]


def tree_of_thought_math(question: str, budget: CallCounter) -> str:
    raw = budgeted_call(tree_of_thought_prompt(question), budget, temperature=0.3)
    return normalize_answer(raw, question, "math")


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

    second_prompt = decomposition_prompt(question) if route == "math" else hidden_cot_prompt(
        question,
        route,
        "independent check",
    )
    second_raw = budgeted_call(second_prompt, budget, temperature=0.2)
    second_answer = normalize_answer(second_raw, question, route)

    if first_answer and first_answer == second_answer:
        return first_answer
    
    if first_answer and second_answer:
        if route == "math":
            tree_answer = tree_of_thought_math(question, budget)
            candidates = [first_answer, second_answer]
            if tree_answer:
                candidates.append(tree_answer)
            return verify_candidates(question, route, candidates, budget)
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

    elif route in {"coding", "planning", "future_prediction", "general"}:
        answer = single_pass(question, route, budget)

    else:
        answer = self_consistency(question, route, budget)

    if is_malformed(answer, route):
        return fallback_retry(question, route, answer, budget) or answer

    return answer

if __name__ == "__main__":
    while True:
        q = input("Enter a question (or 'exit'): ")
        if q.lower() == "exit":
            break
        a = invoke_agent(q)
        print(f"AI: {a}\n")

