import re

from typing import Optional
from textblob import TextBlob
from translate import Translator
from tools.decorator import tool

@tool(
    name="clean_text",
    description="Clean and normalize text by removing special characters, extra whitespace, and optionally converting to lowercase.",
    category="text"
)
def clean_text(text: str, lowercase: Optional[bool] = True, remove_punctuation: Optional[bool] = False) -> dict:
    try:
        cleaned = text
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Optionally remove punctuation
        if remove_punctuation:
            cleaned = re.sub(r'[^\w\s]', '', cleaned)
        
        # Optionally convert to lowercase
        if lowercase:
            cleaned = cleaned.lower()
        
        return {
            "original_text": text,
            "cleaned_text": cleaned,
            "original_length": len(text),
            "cleaned_length": len(cleaned)
        }
    except Exception as e:
        return {"error": str(e)}

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

@tool(
    name="translate_text",
    description="Translate text from one language to another.",
    category="text"
)
def translate_text(text: str, source_lang: str, target_lang: str) -> dict:
    try:
        translator = Translator(from_lang=source_lang, to_lang=target_lang)
        translated_text = translator.translate(text)
        return {
            "original_text": text,
            "translated_text": translated_text,
            "source_language": source_lang,
            "target_language": target_lang
        }
    except Exception as e:
        return {"error": str(e)}