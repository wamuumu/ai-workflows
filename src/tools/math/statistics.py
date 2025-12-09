import numpy as np

from tools.decorator import tool

@tool(
    name="compute_statistics",
    description="Compute descriptive statistics (mean, median, std, variance, min, max) for numerical data.",
    category="math"
)
def compute_statistics(data: list) -> dict:
    try:
        if not data or not isinstance(data, list):
            return {"error": "Input must be a non-empty list of numbers."}
        
        data_array = np.array(data, dtype=float)
        
        return {
            "count": int(len(data_array)),
            "mean": float(np.mean(data_array)),
            "median": float(np.median(data_array)),
            "std": float(np.std(data_array)),
            "variance": float(np.var(data_array)),
            "min": float(np.min(data_array)),
            "max": float(np.max(data_array)),
            "sum": float(np.sum(data_array))
        }
    except Exception as e:
        return {"error": str(e)}