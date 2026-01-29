"""
Machine Learning Tools Module
=============================

This module provides machine learning tools for text embedding,
clustering, regression, and prediction tasks.

Main Responsibilities:
    - Convert text to numerical embeddings (TF-IDF)
    - Cluster data using K-Means algorithm
    - Train linear regression models
    - Make predictions using trained model parameters

Key Dependencies:
    - numpy: Numerical computing
    - sklearn: Machine learning algorithms
    - tools.decorator: For @tool registration

ML Algorithms:
    - TF-IDF: Text feature extraction
    - K-Means: Unsupervised clustering
    - Linear Regression: Supervised regression
"""

import numpy as np

from typing import TypedDict, List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.linear_model import LinearRegression
from tools.decorator import tool


class EmbeddingOutput(TypedDict):
    """
    Structured output for text embeddings.
    
    Attributes:
        embeddings: List of embedding vectors for each input text.
        feature_names: List of feature/token names in the vocabulary.
        shape: Tuple of (n_samples, n_features) dimensions.
    """
    embeddings: List[List[float]]
    feature_names: List[str]
    shape: tuple


class ClusteringOutput(TypedDict):
    """
    Structured output for clustering results.
    
    Attributes:
        labels: Cluster assignment for each data point.
        cluster_centers: Centroid coordinates for each cluster.
        n_clusters: Number of clusters used.
        inertia: Sum of squared distances to nearest cluster center.
    """
    labels: List[int]
    cluster_centers: List[List[float]]
    n_clusters: int
    inertia: float


class RegressionOutput(TypedDict):
    """
    Structured output for regression training.
    
    Attributes:
        coefficients: Model coefficients for each feature.
        intercept: Model intercept (bias) term.
        r2_score: Coefficient of determination (R²).
        n_features: Number of input features.
        n_samples: Number of training samples.
    """
    coefficients: List[float]
    intercept: float
    r2_score: float
    n_features: int
    n_samples: int


class PredictionOutput(TypedDict):
    """
    Structured output for predictions.
    
    Attributes:
        predictions: List of predicted values.
        n_predictions: Number of predictions made.
    """
    predictions: List[float]
    n_predictions: int


@tool(
    name="embed_text",
    description="Convert texts into numerical embeddings using TF-IDF vectorization.",
    category="ml"
)
def embed_text(texts: list, max_features: int = 100) -> EmbeddingOutput:
    """
    Convert text documents to TF-IDF embeddings.
    
    Transforms a list of text documents into numerical vectors
    using Term Frequency-Inverse Document Frequency weighting.
    
    Args:
        texts: List of text documents to embed.
        max_features: Maximum vocabulary size (default: 100).
        
    Returns:
        EmbeddingOutput with embeddings, feature names, and shape.
        Returns error dict if input is invalid.
    """
    try:
        # Validate input
        if not texts or not isinstance(texts, list):
            return {"error": "Input must be a non-empty list of texts."}
        
        # Fit TF-IDF vectorizer and transform texts
        vectorizer = TfidfVectorizer(max_features=max_features)
        embeddings = vectorizer.fit_transform(texts)
        
        return EmbeddingOutput(
            embeddings=embeddings.toarray().tolist(),
            feature_names=vectorizer.get_feature_names_out().tolist(),
            shape=embeddings.shape
        )
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="cluster_data",
    description="Cluster numerical data using K-Means algorithm.",
    category="ml"
)
def cluster_data(data: list, n_clusters: int = 3) -> ClusteringOutput:
    """
    Cluster data points using K-Means algorithm.
    
    Groups similar data points into clusters based on Euclidean
    distance to cluster centroids.
    
    Args:
        data: List of numerical vectors to cluster.
        n_clusters: Number of clusters to form (default: 3).
        
    Returns:
        ClusteringOutput with labels, centers, and inertia.
        Returns error dict if input is invalid.
    """
    try:
        # Validate input
        if not data or not isinstance(data, list):
            return {"error": "Input must be a non-empty list of numerical vectors."}
        
        data_array = np.array(data)
        
        # Ensure 2D array for sklearn
        if len(data_array.shape) == 1:
            data_array = data_array.reshape(-1, 1)
        
        # Fit K-Means model
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(data_array)
        
        return ClusteringOutput(
            labels=labels.tolist(),
            cluster_centers=kmeans.cluster_centers_.tolist(),
            n_clusters=kmeans.n_clusters,
            inertia=float(kmeans.inertia_)
        )
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="train_regression",
    description="Train a linear regression model on provided data and return model coefficients and R² score.",
    category="ml"
)
def train_regression(X: list, y: list) -> RegressionOutput:
    """
    Train a linear regression model.
    
    Fits a linear regression model to the provided features and
    target values, returning the learned parameters.
    
    Args:
        X: List of feature vectors (2D) or values (1D).
        y: List of target values.
        
    Returns:
        RegressionOutput with coefficients, intercept, and R² score.
        Returns error dict if input is invalid.
    """
    try:
        # Validate inputs
        if not X or not y or len(X) != len(y):
            return {"error": "X and y must be non-empty lists of the same length."}
        
        X_array = np.array(X)
        y_array = np.array(y)
        
        # Ensure X is 2D for sklearn
        if len(X_array.shape) == 1:
            X_array = X_array.reshape(-1, 1)
        
        # Fit linear regression model
        model = LinearRegression()
        model.fit(X_array, y_array)
        
        # Calculate R² score
        r2_score = model.score(X_array, y_array)
        
        return RegressionOutput(
            coefficients=model.coef_.tolist() if hasattr(model.coef_, 'tolist') else [float(model.coef_)],
            intercept=float(model.intercept_),
            r2_score=float(r2_score),
            n_features=X_array.shape[1] if len(X_array.shape) > 1 else 1,
            n_samples=len(y_array)
        )
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="make_predictions",
    description="Make predictions using linear regression model parameters (coefficients and intercept).",
    category="ml"
)
def make_predictions(X: list, coefficients: list, intercept: float) -> PredictionOutput:
    """
    Make predictions using trained regression parameters.
    
    Applies the linear regression equation y = X * coef + intercept
    to generate predictions for new data.
    
    Args:
        X: List of feature vectors to predict for.
        coefficients: Model coefficients from training.
        intercept: Model intercept from training.
        
    Returns:
        PredictionOutput with predictions and count.
        Returns error dict if input is invalid.
    """
    try:
        # Validate inputs
        if not X or not coefficients:
            return {"error": "X and coefficients must be provided."}
        
        X_array = np.array(X)
        coef_array = np.array(coefficients)
        
        # Ensure X is 2D for matrix multiplication
        if len(X_array.shape) == 1:
            X_array = X_array.reshape(-1, 1)
        
        # Calculate predictions: y = X * coef + intercept
        predictions = np.dot(X_array, coef_array) + intercept
        
        return PredictionOutput(
            predictions=predictions.tolist() if hasattr(predictions, 'tolist') else [float(predictions)],
            n_predictions=len(predictions) if hasattr(predictions, '__len__') else 1
        )
    except Exception as e:
        return {"error": str(e)}