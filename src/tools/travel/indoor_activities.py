import requests

from geopy.geocoders import Nominatim
from tools.decorator import tool

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