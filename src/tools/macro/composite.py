"""
Composite Macro Tools
=====================

These are higher-level tools that combine multiple atomic tools to perform
complex tasks in a single call. They are designed to reduce workflow complexity
and test how architectures handle macro vs atomic tool selection.

Main Responsibilities:
    - Provide high-level abstractions for common multi-step operations
    - Combine weather, travel, finance, text, and document operations
    - Demonstrate composite tool design patterns

Tool Compositions:
    - plan_trip: Weather + attractions + indoor/outdoor activities
    - write: File writing + email sending
    - analyze_stock_with_news: Stock price + news + sentiment
    - process_text_multilingual: Text cleaning + translation + sentiment
    - research_topic: Web search + news search
    - analyze_documents_batch: File listing + reading + sentiment

Key Dependencies:
    - All atomic tool modules (weather, travel, finance, text, etc.)
    - tools.decorator: For @tool registration
    - tools.tool: For ToolType.MACRO designation

Design Rationale:
    Macro tools trade flexibility for convenience. They encapsulate
    common patterns but may not suit all use cases. The workflow
    generator can choose between atomic and macro tools based on
    the specific requirements of each task.
"""

from typing import TypedDict, List, Optional
from tools.decorator import tool
from tools.tool import ToolType


# ============================================================================
# Output Type Definitions
# ============================================================================

class TripPlanOutput(TypedDict):
    """
    Structured output for trip planning.
    
    Attributes:
        destination: The trip destination city.
        weather_summary: Summary of weather forecast.
        attractions: List of recommended attractions.
        recommended_activities: List of weather-appropriate activities.
        trip_notes: Additional recommendations and notes.
    """
    destination: str
    weather_summary: str
    attractions: List[str]
    recommended_activities: List[str]
    trip_notes: str


class StockAnalysisOutput(TypedDict):
    """
    Structured output for stock analysis.
    
    Attributes:
        symbol: The stock ticker symbol.
        current_price: Current market price.
        recent_news: List of recent news articles.
        sentiment: Overall sentiment assessment.
        analysis_summary: Human-readable analysis summary.
    """
    symbol: str
    current_price: float
    recent_news: List[dict]
    sentiment: str
    analysis_summary: str


class MultilingualTextOutput(TypedDict):
    """
    Structured output for multilingual text processing.
    
    Attributes:
        original_text: The input text.
        cleaned_text: Text after cleaning.
        translations: Dictionary mapping language codes to translations.
        sentiment: Sentiment analysis results.
    """
    original_text: str
    cleaned_text: str
    translations: dict
    sentiment: dict


class ResearchOutput(TypedDict):
    """
    Structured output for topic research.
    
    Attributes:
        topic: The research topic.
        web_results: List of web search results.
        news_results: List of news articles.
        summary: Human-readable research summary.
    """
    topic: str
    web_results: List[dict]
    news_results: List[dict]
    summary: str


class DocumentBatchOutput(TypedDict):
    """
    Structured output for batch document analysis.
    
    Attributes:
        directory: The directory that was processed.
        files_processed: Number of files analyzed.
        results: Per-file analysis results.
        summary: Aggregate sentiment summary.
    """
    directory: str
    files_processed: int
    results: List[dict]
    summary: str


class WriteOutput(TypedDict):
    """
    Structured output for write operations.
    
    Attributes:
        file_written: Whether a file was written.
        email_sent: Whether an email was sent.
        message: Confirmation message.
    """
    file_written: bool
    email_sent: bool
    message: str


# ============================================================================
# Macro Tool Implementations
# ============================================================================

@tool(
    name="plan_trip",
    description="Plan a complete trip by getting weather forecast and filtering activities accordingly.",
    category="planning",
    type=ToolType.MACRO
)
def plan_trip(
    destination: str,
    forecast_days: int = 7,
    num_attractions: int = 5
) -> TripPlanOutput:
    """
    Plan a complete trip with weather-appropriate recommendations.
    
    Combines weather forecasting with attraction and activity discovery
    to provide weather-appropriate recommendations.
    
    Atomic tools combined:
        - current_weather: Get weather forecast
        - get_city_attractions: Find tourist attractions
        - get_indoor_activities / get_outdoor_activities: Based on weather
    
    Args:
        destination: City or location name.
        forecast_days: Number of days to forecast (default: 7).
        num_attractions: Number of attractions/activities to retrieve.
        
    Returns:
        TripPlanOutput with weather, attractions, activities, and notes.
        Returns error dict if critical failure occurs.
    """
    from tools.weather import get_weather
    from tools.travel import get_city_attractions, get_indoor_activities, get_outdoor_activities

    try:
        # Get weather forecast to inform activity selection
        weather = get_weather(destination, forecast_days)
        if "error" in weather:
            weather_summary = f"Weather unavailable: {weather['error']}"
            will_rain = False
        else:
            forecasts = weather.get("forecasts", [])
            will_rain = any("rain" in f.lower() for f in forecasts)
            weather_summary = f"Forecast: {', '.join(forecasts[:3])}..."

        # Get attractions regardless of weather
        attractions_result = get_city_attractions(destination, limit=num_attractions)
        attractions = attractions_result.get("attractions", []) if "error" not in attractions_result else []

        # Select indoor or outdoor activities based on weather
        if will_rain:
            activities_result = get_indoor_activities(destination, limit=num_attractions)
            activity_type = "indoor"
        else:
            activities_result = get_outdoor_activities(destination, limit=num_attractions)
            activity_type = "outdoor"

        activities = activities_result.get("activities", []) if "error" not in activities_result else []

        # Build contextual trip notes
        trip_notes = f"Based on the weather forecast, we recommend {activity_type} activities."
        if will_rain:
            trip_notes += " Rain is expected during your trip, so pack accordingly."

        return TripPlanOutput(
            destination=destination,
            weather_summary=weather_summary,
            attractions=attractions,
            recommended_activities=activities,
            trip_notes=trip_notes
        )
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="write",
    description="Either write a file or an email, or both, based on the provided input.",
    category="utils",
    type=ToolType.MACRO
)
def write(
    file_path: Optional[str] = None,
    content: str = "",
    recipient: Optional[str] = None,
    subject: Optional[str] = "No Subject"
) -> WriteOutput:
    """
    Write content to a file and/or send via email.
    
    Flexible output macro that can write to file, send email, or both
    depending on which parameters are provided.
    
    Atomic tools combined:
        - write_file: File system writing
        - send_email: Email sending
    
    Args:
        file_path: Path for file output (optional).
        content: Content to write/send (required).
        recipient: Email recipient address (optional).
        subject: Email subject line (default: "No Subject").
        
    Returns:
        WriteOutput indicating which operations were performed.
        Returns error dict if neither file_path nor recipient provided.
    """
    from tools.documents import write_file
    from tools.communication import send_email

    file_out = None
    email_out = None
    
    # Validate that at least one output is specified
    if not file_path and not recipient:
        return {"error": "At least one of file_path or recipient must be provided."}
    elif not content:
        return {"error": "Content to write/send must be provided."}
    
    # Perform both operations if both are specified
    elif recipient and file_path:
        file_out = write_file(file_path, content)
        email_out = send_email(recipient, subject, content)
    
    # Email only
    elif recipient and not file_path:
        email_out = send_email(recipient, subject, content)
    
    # File only
    elif file_path and not recipient:
        file_out = write_file(file_path, content)

    return WriteOutput(
        file_written=True if file_out else False,
        email_sent=True if email_out else False,
        message=email_out.get("message") if email_out else ""
    )


@tool(
    name="analyze_stock_with_news",
    description="Analyze a stock by getting its current price, recent news, and sentiment analysis of the news.",
    category="finance",
    type=ToolType.MACRO
)
def analyze_stock_with_news(
    symbol: str,
    news_count: int = 5
) -> StockAnalysisOutput:
    """
    Perform comprehensive stock analysis with news sentiment.
    
    Combines price lookup, news retrieval, and sentiment analysis
    to provide a holistic view of a stock's current situation.
    
    Atomic tools combined:
        - get_stock_price: Current market price
        - get_news: Recent news articles
        - analyze_sentiment: Headline sentiment scoring
    
    Args:
        symbol: Stock ticker symbol (e.g., "AAPL").
        news_count: Number of news articles to analyze (default: 5).
        
    Returns:
        StockAnalysisOutput with price, news, sentiment, and summary.
        Returns error dict if critical failure occurs.
    """
    from tools.finance import get_stock_price
    from tools.news import get_news
    from tools.text import analyze_sentiment

    try:
        # Get current stock price
        price_result = get_stock_price(symbol)
        if "error" in price_result:
            current_price = 0.0
        else:
            current_price = price_result.get("price", 0.0)

        # Get recent news about the stock
        news_result = get_news(f"{symbol} stock", max_results=news_count)
        news_items = news_result.get("news", []) if "error" not in news_result else []

        # Analyze sentiment of each news headline
        sentiments = []
        for news_item in news_items:
            title = news_item.get("title", "")
            if title:
                sentiment_result = analyze_sentiment(title)
                if "error" not in sentiment_result:
                    sentiments.append(sentiment_result.get("polarity", 0))

        # Aggregate sentiment scores into overall assessment
        if sentiments:
            avg_sentiment = sum(sentiments) / len(sentiments)
            if avg_sentiment > 0.1:
                overall_sentiment = "positive"
            elif avg_sentiment < -0.1:
                overall_sentiment = "negative"
            else:
                overall_sentiment = "neutral"
        else:
            overall_sentiment = "unknown"

        # Build human-readable summary
        summary = f"{symbol} is trading at ${current_price:.2f}. "
        summary += f"Based on {len(news_items)} recent news articles, market sentiment appears {overall_sentiment}."

        return StockAnalysisOutput(
            symbol=symbol,
            current_price=current_price,
            recent_news=news_items[:3],  # Limit for output size
            sentiment=overall_sentiment,
            analysis_summary=summary
        )
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="process_text_multilingual",
    description="Process text by cleaning, translating to multiple languages, and analyzing sentiment.",
    category="text",
    type=ToolType.MACRO
)
def process_text_multilingual(
    text: str,
    target_languages: Optional[List[str]] = None,
    source_language: str = "en"
) -> MultilingualTextOutput:
    """
    Process text with cleaning, translation, and sentiment analysis.
    
    Combines text normalization, multi-language translation, and
    sentiment analysis into a single comprehensive operation.
    
    Atomic tools combined:
        - clean_text: Text normalization
        - translate_text: Language translation (multiple calls)
        - analyze_sentiment: Sentiment scoring
    
    Args:
        text: Input text to process.
        target_languages: List of language codes to translate to
            (default: ["es", "fr", "de"]).
        source_language: Source language code (default: "en").
        
    Returns:
        MultilingualTextOutput with cleaned text, translations, and sentiment.
        Returns error dict if critical failure occurs.
    """
    from tools.text import clean_text, translate_text, analyze_sentiment

    # Default target languages if not specified
    if target_languages is None:
        target_languages = ["es", "fr", "de"]

    try:
        # Clean the text first for consistent processing
        clean_result = clean_text(text, lowercase=False, remove_punctuation=False)
        cleaned = clean_result.get("cleaned_text", text) if "error" not in clean_result else text

        # Translate to each target language
        translations = {}
        for lang in target_languages:
            trans_result = translate_text(cleaned, source_language, lang)
            if "error" not in trans_result:
                translations[lang] = trans_result.get("translated_text", "")
            else:
                translations[lang] = f"Translation failed: {trans_result.get('error', 'unknown')}"

        # Analyze sentiment of original (cleaned) text
        sentiment_result = analyze_sentiment(cleaned)
        sentiment_info = {
            "polarity": sentiment_result.get("polarity", 0),
            "label": sentiment_result.get("label", "unknown")
        } if "error" not in sentiment_result else {"error": sentiment_result.get("error")}

        return MultilingualTextOutput(
            original_text=text,
            cleaned_text=cleaned,
            translations=translations,
            sentiment=sentiment_info
        )
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="research_topic",
    description="Research a topic by searching the web and news, then summarizing the findings.",
    category="research",
    type=ToolType.MACRO
)
def research_topic(
    topic: str,
    web_results: int = 5,
    news_results: int = 5
) -> ResearchOutput:
    """
    Research a topic using web and news searches.
    
    Combines web search and news search to gather comprehensive
    information about a topic from multiple sources.
    
    Atomic tools combined:
        - search_web: General web search
        - get_news: News article search
    
    Args:
        topic: Topic to research.
        web_results: Number of web results to retrieve (default: 5).
        news_results: Number of news results to retrieve (default: 5).
        
    Returns:
        ResearchOutput with web results, news results, and summary.
        Returns error dict if critical failure occurs.
    """
    from tools.web import search_web
    from tools.news import get_news

    try:
        # Search the web for general information
        web_result = search_web(topic, num_results=web_results)
        web_items = web_result.get("results", []) if "error" not in web_result else []

        # Search news for recent coverage
        news_result = get_news(topic, max_results=news_results)
        news_items = news_result.get("news", []) if "error" not in news_result else []

        # Build human-readable summary
        summary_parts = [f"Research findings for '{topic}':"]
        summary_parts.append(f"- Found {len(web_items)} web results")
        summary_parts.append(f"- Found {len(news_items)} news articles")

        if web_items:
            summary_parts.append(f"- Top web result: {web_items[0].get('title', 'N/A')}")
        if news_items:
            summary_parts.append(f"- Latest news: {news_items[0].get('title', 'N/A')}")

        return ResearchOutput(
            topic=topic,
            web_results=web_items,
            news_results=news_items,
            summary="\n".join(summary_parts)
        )
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="analyze_documents_batch",
    description="Analyze multiple documents in a directory by reading each file and performing sentiment analysis.",
    category="documents",
    type=ToolType.MACRO
)
def analyze_documents_batch(
    directory_path: str,
    extension: str = ".txt"
) -> DocumentBatchOutput:
    """
    Batch analyze documents in a directory for sentiment.
    
    Processes all matching files in a directory, reading content
    and performing sentiment analysis on each.
    
    Atomic tools combined:
        - list_files: Directory listing
        - read_file: File content reading
        - analyze_sentiment: Sentiment scoring
    
    Args:
        directory_path: Path to directory containing documents.
        extension: File extension filter (default: ".txt").
        
    Returns:
        DocumentBatchOutput with per-file results and aggregate summary.
        Returns error dict if directory listing fails.
    """
    from tools.documents import list_files, read_file
    from tools.text import analyze_sentiment

    try:
        # List files in directory with extension filter
        files_result = list_files(directory_path, extension=extension)
        if "error" in files_result:
            return {"error": files_result["error"]}

        files = files_result.get("files", [])
        results = []

        # Process each file
        for file_path in files:
            try:
                # Read file content
                read_result = read_file(file_path)
                if "error" in read_result:
                    results.append({
                        "file": file_path,
                        "status": "error",
                        "error": read_result["error"]
                    })
                    continue

                content = read_result.get("content", "")

                # Analyze sentiment of file content
                sentiment_result = analyze_sentiment(content)
                sentiment = sentiment_result.get("label", "unknown") if "error" not in sentiment_result else "error"
                polarity = sentiment_result.get("polarity", 0) if "error" not in sentiment_result else 0

                results.append({
                    "file": file_path,
                    "status": "success",
                    "sentiment": sentiment,
                    "polarity": polarity,
                    "length": len(content)
                })
            except Exception as file_error:
                results.append({
                    "file": file_path,
                    "status": "error",
                    "error": str(file_error)
                })

        # Build aggregate summary
        successful = [r for r in results if r.get("status") == "success"]
        positive = sum(1 for r in successful if r.get("sentiment") == "positive")
        negative = sum(1 for r in successful if r.get("sentiment") == "negative")
        neutral = sum(1 for r in successful if r.get("sentiment") == "neutral")

        summary = f"Processed {len(files)} files. "
        summary += f"Sentiment breakdown: {positive} positive, {negative} negative, {neutral} neutral."

        return DocumentBatchOutput(
            directory=directory_path,
            files_processed=len(files),
            results=results,
            summary=summary
        )
    except Exception as e:
        return {"error": str(e)}
