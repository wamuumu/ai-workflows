import re

from typing import Optional
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