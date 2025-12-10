import requests

from geopy.geocoders import Nominatim
from tools.decorator import tool

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

@tool(
    name="current_weather", 
    description="Get the current weather for a specified location for a certain amount of days.",    
    category="weather"
)
def get_weather(location: str, forecast_days: int = 7) -> dict: 
    try:
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(location)
        
        lat = location.latitude
        lon = location.longitude

        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&forecast_days={forecast_days}&daily=temperature_2m_max,temperature_2m_min,weathercode&timezone=auto"
        weather_response = requests.get(weather_url, timeout=5)
        weather_response.raise_for_status()
        weather_data = weather_response.json()
        weather_data['daily']['weather_labels'] = [WEATHER_CODE_LABELS.get(code, "unknown") for code in weather_data['daily']['weathercode']]

        return weather_data
    except Exception as e:
        return {"error": str(e)}
