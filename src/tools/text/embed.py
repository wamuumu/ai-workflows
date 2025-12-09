from tools.decorator import tool
from sklearn.feature_extraction.text import TfidfVectorizer

@tool(
    name="embed_text",
    description="Convert texts into numerical embeddings using TF-IDF vectorization.",
    category="text"
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