import re
import numpy as np

from typing import TypedDict
from tools.decorator import tool

class CalculatorOutput(TypedDict):
    result: float

class StatisticsOutput(TypedDict):
    count: int
    mean: float
    median: float
    std: float
    variance: float
    min: float
    max: float
    sum: float

@tool(
    name="calculator",
    description="Evaluate a mathematical expression and return the result.",
    category="math",
)
def calculator(expression: str) -> CalculatorOutput:
    expression = re.sub(r'[^0-9+\-*/().]', '', expression)
    try:
        return CalculatorOutput(result=float(eval(expression)))
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="compute_statistics",
    description="Compute descriptive statistics (mean, median, std, variance, min, max) for numerical data.",
    category="math"
)
def compute_statistics(data: list) -> StatisticsOutput:
    try:
        if not data or not isinstance(data, list):
            return {"error": "Input must be a non-empty list of numbers."}
        
        data_array = np.array(data, dtype=float)
        
        return StatisticsOutput(
            count=int(len(data_array)),
            mean=float(np.mean(data_array)),
            median=float(np.median(data_array)),
            std=float(np.std(data_array)),
            variance=float(np.var(data_array)),
            min=float(np.min(data_array)),
            max=float(np.max(data_array)),
            sum=float(np.sum(data_array))
        )
    except Exception as e:
        return {"error": str(e)}