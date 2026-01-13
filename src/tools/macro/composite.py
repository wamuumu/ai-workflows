"""
Composite Macro Tools

These are higher-level tools that combine multiple atomic tools to perform
complex tasks in a single call. They are designed to reduce workflow complexity
and test how architectures handle macro vs atomic tool selection.
"""

from typing import TypedDict, List, Optional
from tools.decorator import tool


# ============================================================================
# Output Type Definitions
# ============================================================================

class TripPlanOutput(TypedDict):
    destination: str
    weather_summary: str
    attractions: List[str]
    recommended_activities: List[str]
    trip_notes: str


class StockAnalysisOutput(TypedDict):
    symbol: str
    current_price: float
    recent_news: List[dict]
    sentiment: str
    analysis_summary: str


class MultilingualTextOutput(TypedDict):
    original_text: str
    cleaned_text: str
    translations: dict
    sentiment: dict


class ResearchOutput(TypedDict):
    topic: str
    web_results: List[dict]
    news_results: List[dict]
    summary: str


class DocumentBatchOutput(TypedDict):
    directory: str
    files_processed: int
    results: List[dict]
    summary: str


# ============================================================================
# Macro Tool Implementations
# ============================================================================

@tool(
    name="plan_trip",
    description="Plan a complete trip by getting weather forecast, attractions, and activity recommendations for a destination.",
    category="planning",
    type="macro"
)
def plan_trip(
    destination: str,
    forecast_days: int = 7,
    num_attractions: int = 5
) -> TripPlanOutput:
    """
    Combines: current_weather, get_city_attractions, get_indoor_activities, get_outdoor_activities
    """
    from tools.weather import get_weather
    from tools.travel import get_city_attractions, get_indoor_activities, get_outdoor_activities

    try:
        # Get weather forecast
        weather = get_weather(destination, forecast_days)
        if "error" in weather:
            weather_summary = f"Weather unavailable: {weather['error']}"
            will_rain = False
        else:
            forecasts = weather.get("forecasts", [])
            will_rain = any("rain" in f.lower() for f in forecasts)
            weather_summary = f"Forecast: {', '.join(forecasts[:3])}..."

        # Get attractions
        attractions_result = get_city_attractions(destination, limit=num_attractions)
        attractions = attractions_result.get("attractions", []) if "error" not in attractions_result else []

        # Get activities based on weather
        if will_rain:
            activities_result = get_indoor_activities(destination, limit=num_attractions)
            activity_type = "indoor"
        else:
            activities_result = get_outdoor_activities(destination, limit=num_attractions)
            activity_type = "outdoor"

        activities = activities_result.get("activities", []) if "error" not in activities_result else []

        # Build trip notes
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
    name="analyze_stock_with_news",
    description="Analyze a stock by getting its current price, recent news, and sentiment analysis of the news.",
    category="finance",
    type="macro"
)
def analyze_stock_with_news(
    symbol: str,
    news_count: int = 5
) -> StockAnalysisOutput:
    """
    Combines: get_stock_price, get_news, analyze_sentiment
    """
    from tools.finance import get_stock_price
    from tools.news import get_news
    from tools.text import analyze_sentiment

    try:
        # Get stock price
        price_result = get_stock_price(symbol)
        if "error" in price_result:
            current_price = 0.0
        else:
            current_price = price_result.get("price", 0.0)

        # Get news about the stock
        company_name = symbol  # Could enhance with a lookup
        news_result = get_news(f"{symbol} stock", max_results=news_count)
        news_items = news_result.get("news", []) if "error" not in news_result else []

        # Analyze sentiment of news headlines
        sentiments = []
        for news_item in news_items:
            title = news_item.get("title", "")
            if title:
                sentiment_result = analyze_sentiment(title)
                if "error" not in sentiment_result:
                    sentiments.append(sentiment_result.get("polarity", 0))

        # Aggregate sentiment
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

        # Build summary
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
    type="macro"
)
def process_text_multilingual(
    text: str,
    target_languages: Optional[List[str]] = None,
    source_language: str = "en"
) -> MultilingualTextOutput:
    """
    Combines: clean_text, translate_text, analyze_sentiment
    """
    from tools.text import clean_text, translate_text, analyze_sentiment

    if target_languages is None:
        target_languages = ["es", "fr", "de"]

    try:
        # Clean the text first
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

        # Analyze sentiment of original text
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
    type="macro"
)
def research_topic(
    topic: str,
    web_results: int = 5,
    news_results: int = 5
) -> ResearchOutput:
    """
    Combines: search_web, get_news
    """
    from tools.web import search_web
    from tools.news import get_news

    try:
        # Search the web
        web_result = search_web(topic, num_results=web_results)
        web_items = web_result.get("results", []) if "error" not in web_result else []

        # Search news
        news_result = get_news(topic, max_results=news_results)
        news_items = news_result.get("news", []) if "error" not in news_result else []

        # Build summary
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
    type="macro"
)
def analyze_documents_batch(
    directory_path: str,
    extension: str = ".txt"
) -> DocumentBatchOutput:
    """
    Combines: list_files, read_file, analyze_sentiment
    """
    from tools.documents import list_files, read_file
    from tools.text import analyze_sentiment

    try:
        # List files in directory
        files_result = list_files(directory_path, extension=extension)
        if "error" in files_result:
            return {"error": files_result["error"]}

        files = files_result.get("files", [])
        results = []

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

                # Analyze sentiment
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

        # Build summary
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
