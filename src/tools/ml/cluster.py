import numpy as np

from tools.decorator import tool
from sklearn.cluster import KMeans

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