import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from tools.decorator import tool

@tool(
    name="embed_text",
    description="Convert texts into numerical embeddings using TF-IDF vectorization.",
    category="ml"
)
def embed_text(texts: list, max_features: int = 100) -> dict:
    try:
        if not texts or not isinstance(texts, list):
            return {"error": "Input must be a non-empty list of texts."}
        
        vectorizer = TfidfVectorizer(max_features=max_features)
        embeddings = vectorizer.fit_transform(texts)
        
        return {
            "embeddings": embeddings.toarray().tolist(),
            "feature_names": vectorizer.get_feature_names_out().tolist(),
            "shape": embeddings.shape
        }
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="cluster_data",
    description="Cluster numerical data using K-Means algorithm.",
    category="ml"
)
def cluster_data(data: list, n_clusters: int = 3) -> dict:
    try:
        if not data or not isinstance(data, list):
            return {"error": "Input must be a non-empty list of numerical vectors."}
        
        data_array = np.array(data)
        if len(data_array.shape) == 1:
            data_array = data_array.reshape(-1, 1)
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(data_array)
        
        return {
            "labels": labels.tolist(),
            "cluster_centers": kmeans.cluster_centers_.tolist(),
            "n_clusters": n_clusters,
            "inertia": float(kmeans.inertia_)
        }
    except Exception as e:
        return {"error": str(e)}

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