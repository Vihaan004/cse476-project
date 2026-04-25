from agent.client import call_model
from agent.normalize_answer import normalize_answer
from agent.call_counter import CallCounter
from agent.router import route_question


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


def self_consistency(question: str, route: str, budget: CallCounter) -> str:
    first_raw = budgeted_call(
        hidden_cot_prompt(question, route),
        budget,
        temperature=0.0,
    )
    first_answer = normalize_answer(first_raw, question)

    second_raw = budgeted_call(
        hidden_cot_prompt(question, route, "independent check"),
        budget,
        temperature=0.2,
    )
    second_answer = normalize_answer(second_raw, question)

    if first_answer and first_answer == second_answer:
        return first_answer

    return first_answer or second_answer

def invoke_agent(question: str) -> str:
    budget = CallCounter(max_calls=20)
    route = route_question(question)
    return self_consistency(question, route, budget)
