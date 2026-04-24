from agent.client import call_model


def invoke_agent(question: str) -> str:
    prompt = f"""
Answer the following question.

Return only the final answer.
Do not include reasoning, explanation, or extra text.

Question:
{question}
""".strip()

    return call_model(prompt)
