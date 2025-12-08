import requests

from geopy.geocoders import Nominatim
from tools.decorator import tool

@tool(
    name="get_city_attractions",
    description="Get a list of popular tourist attractions in a given city.",
    category="travel"
)
def get_city_attractions(city: str, limit: int = 10) -> dict:
    try:
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(city)
        
        lat = location.latitude
        lon = location.longitude

        api_key = "960f23468e46413b90c52f435dc8b1de"
        attractions_url = f"https://api.geoapify.com/v2/places?categories=tourism.sights&bias=proximity:{lon},{lat}&limit={limit}&apiKey={api_key}"
        attractions_response = requests.get(attractions_url, timeout=10)
        attractions_response.raise_for_status()
        attractions_data = attractions_response.json()

        attractions = set()
        for feature in attractions_data.get('features', []):
            attractions.add(feature['properties']['name'])
        
        return {"attractions": list(attractions)}
    except Exception as e:
        return {"error": str(e)}