from agent.client import call_model
from agent.normalize_answer import normalize_answer
from agent.call_counter import CallCounter

def budgeted_call(prompt: str, budget: CallCounter) -> str | None:
    if not budget.record():
        return None

    return call_model(prompt)

def invoke_agent(question: str) -> str:
    budget = CallCounter(max_calls=20)
    best_answer = ""
    prompt = f"""
    Solve the following problem according to your given instructions. 
    Dont include any explanations or reasoning steps, just return the final accurate answer.  
    Question:{question}""".strip()
    
    raw = budgeted_call(prompt, budget)
    
    if raw is not None:
        best_answer = normalize_answer(raw, question)

    return best_answer