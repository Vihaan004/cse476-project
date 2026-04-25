from agent.client import call_model
from agent.normalize_answer import normalize_answer
from agent.call_counter import CallCounter
from agent.router import route_question


PROMPTS = {
    "math": (
        "Solve carefully step by step internally. "
        "Return only the final numeric answer."
    ),
    "mcq": (
        "Think through each option internally. "
        "Return only the answer text."
    ),
    "yes_no": (
        "Reason carefully internally. "
        "Answer with only yes or no."
    ),
    "general": (
        "Reason carefully internally. "
        "Return only the final answer. Do not include explanations."
    ),
}


def hidden_cot_prompt(question: str, route: str) -> str:
    instruction = PROMPTS.get(route, PROMPTS["general"])
    return f"""
    {instruction}
    Question:{question}""".strip()


def budgeted_call(prompt: str, budget: CallCounter) -> str | None:
    if not budget.record():
        return None

    return call_model(prompt)

def invoke_agent(question: str) -> str:
    budget = CallCounter(max_calls=20)
    best_answer = ""
    route = route_question(question)
    prompt = hidden_cot_prompt(question, route)
    
    raw = budgeted_call(prompt, budget)
    
    if raw is not None:
        best_answer = normalize_answer(raw, question)

    return best_answer
