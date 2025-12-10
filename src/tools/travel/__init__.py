import requests

from geopy.geocoders import Nominatim
from tools.decorator import tool

@tool(
    name="get_city_attractions",
    description="Get a list of popular tourist attractions in a given city.",
    category="travel"
)
def get_city_attractions(city: str, limit: int = 10) -> list:
    try:
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(city)
        
        lat = location.latitude
        lon = location.longitude

        api_key = "960f23468e46413b90c52f435dc8b1de"
        categories = "tourism.sights"
        attractions_url = f"https://api.geoapify.com/v2/places?categories={categories}&bias=proximity:{lon},{lat}&limit={limit}&apiKey={api_key}"
        attractions_response = requests.get(attractions_url, timeout=10)
        attractions_response.raise_for_status()
        attractions_data = attractions_response.json()

        attractions = set()
        for feature in attractions_data.get('features', []):
            name = feature['properties'].get('name', None)
            if name:
                attractions.add(name)
        
        return list(attractions)
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="get_indoor_activities",
    description="Get a list of indoor activities and venues in a given city (museums, theaters, shopping malls, etc.).",
    category="travel"
)
def get_indoor_activities(city: str, limit: int = 10) -> list:
    try:
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(city)
        
        lat = location.latitude
        lon = location.longitude

        api_key = "960f23468e46413b90c52f435dc8b1de"
        categories = "entertainment.museum,entertainment.culture,entertainment.amusement_arcade,entertainment.aquarium,entertainment.cinema,commercial.shopping_mall"
        activities_url = f"https://api.geoapify.com/v2/places?categories={categories}&bias=proximity:{lon},{lat}&limit={limit}&apiKey={api_key}"
        activities_response = requests.get(activities_url, timeout=10)
        activities_response.raise_for_status()
        activities_data = activities_response.json()

        activities = set()
        for feature in activities_data.get('features', []):
            name = feature['properties'].get('name', None)
            if name:
                activities.add(name)
        
        return list(activities)
    except Exception as e:
        return {"error": str(e)}

@tool(
    name="get_outdoor_activities",
    description="Get a list of outdoor activities and venues in a given city (parks, hiking trails, sports facilities, etc.).",
    category="travel"
)
def get_outdoor_activities(city: str, limit: int = 10) -> list:
    try:
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(city)
        
        lat = location.latitude
        lon = location.longitude

        api_key = "960f23468e46413b90c52f435dc8b1de"
        categories = "leisure,highway,natural,national_park,camping,beach,sport,ski,commercial.outdoor_and_sport"
        activities_url = f"https://api.geoapify.com/v2/places?categories={categories}&bias=proximity:{lon},{lat}&limit={limit}&apiKey={api_key}"
        activities_response = requests.get(activities_url, timeout=10)
        activities_response.raise_for_status()
        activities_data = activities_response.json()

        activities = set()
        for feature in activities_data.get('features', []):
            name = feature['properties'].get('name', None)
            if name:
                activities.add(name)
        
        return list(activities)
    except Exception as e:
        return {"error": str(e)}