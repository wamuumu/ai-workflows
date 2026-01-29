"""
Text Tools Module
=================

This module provides text processing tools for cleaning, sentiment
analysis, and translation operations.

Main Responsibilities:
    - Clean and normalize text input
    - Analyze sentiment polarity of text
    - Translate text between languages

Key Dependencies:
    - re: Regular expression operations
    - textblob: Natural language processing and sentiment
    - translate: Translation API wrapper
    - tools.decorator: For @tool registration
"""

import re

from typing import TypedDict, Optional
from textblob import TextBlob
from translate import Translator
from tools.decorator import tool


class CleanTextOutput(TypedDict):
    """
    Structured output for text cleaning.
    
    Attributes:
        original_text: The input text before cleaning.
        cleaned_text: The text after cleaning operations.
        original_length: Character count of original text.
        cleaned_length: Character count of cleaned text.
    """
    original_text: str
    cleaned_text: str
    original_length: int
    cleaned_length: int


class AnalyzeSentimentOutput(TypedDict):
    """
    Structured output for sentiment analysis.
    
    Attributes:
        polarity: Sentiment score from -1.0 (negative) to 1.0 (positive).
        label: Classification label ("positive", "negative", "neutral").
    """
    polarity: float
    label: str


class TranslateTextOutput(TypedDict):
    """
    Structured output for text translation.
    
    Attributes:
        original_text: The input text in source language.
        translated_text: The translated text in target language.
        source_language: The source language code.
        target_language: The target language code.
    """
    original_text: str
    translated_text: str
    source_language: str
    target_language: str


@tool(
    name="clean_text",
    description="Clean and normalize text by removing special characters, extra whitespace, and optionally converting to lowercase.",
    category="text"
)
def clean_text(text: str, lowercase: Optional[bool] = True, remove_punctuation: Optional[bool] = False) -> CleanTextOutput:
    """
    Clean and normalize text input.
    
    Performs text normalization including whitespace removal,
    optional punctuation removal, and case conversion.
    
    Args:
        text: The input text to clean.
        lowercase: Whether to convert to lowercase (default: True).
        remove_punctuation: Whether to remove punctuation (default: False).
        
    Returns:
        CleanTextOutput with original and cleaned text plus lengths.
        Returns error dict if processing fails.
    """
    try:
        cleaned = text
        
        # Remove extra whitespace and trim
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Optionally remove punctuation characters
        if remove_punctuation:
            cleaned = re.sub(r'[^\w\s]', '', cleaned)
        
        # Optionally convert to lowercase
        if lowercase:
            cleaned = cleaned.lower()
        
        return CleanTextOutput(
            original_text=text,
            cleaned_text=cleaned,
            original_length=len(text),
            cleaned_length=len(cleaned)
        )
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="analyze_sentiment",
    description="Analyze the sentiment of a given text and return polarity and classification label.",
    category="text"
)
def analyze_sentiment(text: str) -> AnalyzeSentimentOutput:
    """
    Analyze the sentiment polarity of text.
    
    Uses TextBlob to compute sentiment polarity score and
    classify the overall sentiment as positive, negative, or neutral.
    
    Args:
        text: The text to analyze for sentiment.
        
    Returns:
        AnalyzeSentimentOutput with polarity score and label.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    
    # Classify based on polarity threshold
    label = "positive" if polarity > 0 else "negative" if polarity < 0 else "neutral"
    return AnalyzeSentimentOutput(polarity=polarity, label=label)


@tool(
    name="translate_text",
    description="Translate text from one language to another.",
    category="text"
)
def translate_text(text: str, source_lang: str, target_lang: str) -> TranslateTextOutput:
    """
    Translate text between languages.
    
    Uses a translation API to convert text from the source
    language to the target language.
    
    Args:
        text: The text to translate.
        source_lang: Source language code (e.g., "en", "es").
        target_lang: Target language code (e.g., "fr", "de").
        
    Returns:
        TranslateTextOutput with original and translated text.
        Returns error dict if translation fails.
    """
    try:
        translator = Translator(from_lang=source_lang, to_lang=target_lang)
        translated_text = translator.translate(text)
        return TranslateTextOutput(
            original_text=text,
            translated_text=translated_text,
            source_language=source_lang,
            target_language=target_lang
        )
    except Exception as e:
        return {"error": str(e)}