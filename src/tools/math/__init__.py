"""
Math Tools Module
=================

This module provides mathematical tools for expression evaluation
and statistical analysis.

Main Responsibilities:
    - Evaluate mathematical expressions safely
    - Compute descriptive statistics on numerical data

Key Dependencies:
    - re: Regular expression for expression sanitization
    - numpy: Numerical computing for statistics
    - tools.decorator: For @tool registration

Security Note:
    The calculator tool sanitizes input by removing non-numeric
    characters before evaluation to prevent code injection.
"""

import re
import numpy as np

from typing import TypedDict
from tools.decorator import tool


class CalculatorOutput(TypedDict):
    """
    Structured output for calculator results.
    
    Attributes:
        result: The computed numerical result.
    """
    result: float


class StatisticsOutput(TypedDict):
    """
    Structured output for statistical analysis.
    
    Attributes:
        count: Number of data points.
        mean: Arithmetic mean of the data.
        median: Median value of the data.
        std: Standard deviation of the data.
        variance: Variance of the data.
        min: Minimum value in the data.
        max: Maximum value in the data.
        sum: Sum of all data values.
    """
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
    """
    Evaluate a mathematical expression.
    
    Sanitizes the input expression by removing all characters except
    digits and basic operators, then evaluates the result.
    
    Args:
        expression: Mathematical expression string (e.g., "2 + 3 * 4").
        
    Returns:
        CalculatorOutput with computed result.
        Returns error dict if evaluation fails.
        
    Security:
        Input is sanitized to allow only: 0-9, +, -, *, /, (, ), .
    """
    # Sanitize expression to prevent code injection
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
    """
    Compute descriptive statistics for numerical data.
    
    Calculates common statistical measures including central tendency
    (mean, median), dispersion (std, variance), and range (min, max).
    
    Args:
        data: List of numerical values to analyze.
        
    Returns:
        StatisticsOutput with all computed statistics.
        Returns error dict if input is invalid or computation fails.
    """
    try:
        # Validate input
        if not data or not isinstance(data, list):
            return {"error": "Input must be a non-empty list of numbers."}
        
        # Convert to numpy array for efficient computation
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