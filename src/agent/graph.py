from agent.client import call_model
from agent.normalize_answer import normalize_answer


def invoke_agent(question: str) -> str:
    prompt = f"""
    Solve the following problem according to your given instructions. 
    Dont include any explanations or reasoning steps, just return the final accurate answer.  
    Question:{question}""".strip()

    return normalize_answer(call_model(prompt), question)