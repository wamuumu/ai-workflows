from textblob import TextBlob
from tools.decorator import tool

@tool(
    name="analyze_sentiment",
    description="Analyze the sentiment of a given text and return polarity and classification label.",
    category="text"
)
def analyze_sentiment(text: str) -> dict:
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    label = "positive" if polarity > 0 else "negative" if polarity < 0 else "neutral"
    return {"polarity": polarity, "label": label}