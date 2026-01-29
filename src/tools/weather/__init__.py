"""
Weather Tools Module
====================

This module provides weather-related tools for retrieving current and
forecast weather data using the Open-Meteo API.

Main Responsibilities:
    - Geocode location names to coordinates
    - Fetch weather forecasts from Open-Meteo API
    - Translate weather codes to human-readable descriptions

Key Dependencies:
    - requests: For HTTP API calls
    - geopy: For location geocoding
    - tools.decorator: For @tool registration

External APIs:
    - Open-Meteo (https://open-meteo.com): Free weather API
    - Nominatim (via geopy): Geocoding service
"""

import requests

from typing import TypedDict, List
from geopy.geocoders import Nominatim
from tools.decorator import tool


# Weather code to human-readable description mapping
# Based on WMO Weather interpretation codes (WW)
WEATHER_CODE_LABELS = {
    0: "clear sky",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "freezing fog",
    51: "light drizzle",
    53: "drizzle",
    55: "dense drizzle",
    56: "freezing drizzle",
    57: "freezing drizzle (dense)",
    61: "slight rain",
    63: "rain",
    65: "heavy rain",
    66: "freezing rain (light)",
    67: "freezing rain (heavy)",
    71: "slight snowfall",
    73: "snowfall",
    75: "heavy snowfall",
    77: "snow grains",
    80: "rain shower (light)",
    81: "rain shower",
    82: "rain shower (heavy)",
    85: "snow shower (light)",
    86: "snow shower (heavy)",
    95: "thunderstorm",
    96: "thunderstorm with hail",
    99: "thunderstorm with heavy hail",
}


class WeatherOutput(TypedDict):
    """
    Structured output for weather forecast data.
    
    Attributes:
        forecasts: List of weather condition descriptions per day.
        max_temps: List of maximum temperatures per day.
        min_temps: List of minimum temperatures per day.
    """
    forecasts: List[str]
    max_temps: List[float]
    min_temps: List[float]


@tool(
    name="current_weather", 
    description="Get the current weather for a specified location for a certain amount of days.",    
    category="weather"
)
def get_weather(location: str, forecast_days: int = 7) -> WeatherOutput: 
    """
    Retrieve weather forecast for a location.
    
    Geocodes the location name to coordinates, then fetches forecast
    data from Open-Meteo API including temperature ranges and conditions.
    
    Args:
        location: City or place name to get weather for.
        forecast_days: Number of days to forecast (default: 7).
        
    Returns:
        WeatherOutput with forecasts, max_temps, and min_temps.
        Returns error dict if request fails.
    """
    try:
        # Geocode location name to coordinates
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(location)
        
        lat = location.latitude
        lon = location.longitude

        # Fetch forecast from Open-Meteo API
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&forecast_days={forecast_days}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto"
        weather_response = requests.get(weather_url, timeout=5)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        
        # Convert weather codes to readable descriptions
        forecasts = [WEATHER_CODE_LABELS.get(code, "unknown") for code in weather_data['daily']['weathercode']]

        return WeatherOutput(
            forecasts=forecasts, 
            max_temps=weather_data['daily']['temperature_2m_max'], 
            min_temps=weather_data['daily']['temperature_2m_min']
        )
    except Exception as e:
        return {"error": str(e)}
