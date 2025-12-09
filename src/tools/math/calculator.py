from tools.decorator import tool

@tool(
    name="calculator",
    description="Evaluate a mathematical expression and return the result.",
    category="math",
)
def calculator(expression: str) -> float:
    try:
        return eval(expression)
    except Exception as e:
        return {"error": str(e)}