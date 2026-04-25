import re

EXPRESSION = re.compile(r"^[0-9+\-*/().\s]+$")

def calculator(expression: str) -> str:
    expression = expression.strip()
    if not EXPRESSION.fullmatch(expression):
        raise ValueError("expression contains unsupported characters")

    value = eval(expression, {"__builtins__": {}}, {})

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    return str(round(value, 6)).rstrip("0").rstrip(".")
