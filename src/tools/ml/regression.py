import numpy as np

from tools.decorator import tool
from sklearn.linear_model import LinearRegression

@tool(
    name="train_regression",
    description="Train a linear regression model on provided data and return model coefficients and R² score.",
    category="ml"
)
def train_regression(X: list, y: list) -> dict:
    try:
        if not X or not y or len(X) != len(y):
            return {"error": "X and y must be non-empty lists of the same length."}
        
        X_array = np.array(X)
        y_array = np.array(y)
        
        # Ensure X is 2D
        if len(X_array.shape) == 1:
            X_array = X_array.reshape(-1, 1)
        
        model = LinearRegression()
        model.fit(X_array, y_array)
        
        r2_score = model.score(X_array, y_array)
        
        return {
            "coefficients": model.coef_.tolist() if hasattr(model.coef_, 'tolist') else [float(model.coef_)],
            "intercept": float(model.intercept_),
            "r2_score": float(r2_score),
            "n_features": X_array.shape[1] if len(X_array.shape) > 1 else 1,
            "n_samples": len(y_array)
        }
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="make_predictions",
    description="Make predictions using linear regression model parameters (coefficients and intercept).",
    category="ml"
)
def make_predictions(X: list, coefficients: list, intercept: float) -> dict:
    try:
        if not X or not coefficients:
            return {"error": "X and coefficients must be provided."}
        
        X_array = np.array(X)
        coef_array = np.array(coefficients)
        
        # Ensure X is 2D
        if len(X_array.shape) == 1:
            X_array = X_array.reshape(-1, 1)
        
        # Calculate predictions: y = X * coef + intercept
        predictions = np.dot(X_array, coef_array) + intercept
        
        return {
            "predictions": predictions.tolist() if hasattr(predictions, 'tolist') else [float(predictions)],
            "n_predictions": len(predictions) if hasattr(predictions, '__len__') else 1
        }
    except Exception as e:
        return {"error": str(e)}