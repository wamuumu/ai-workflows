"""
Travel Tools Module
===================

This module provides travel-related tools for discovering attractions
and activities in cities using the Geoapify Places API.

Main Responsibilities:
    - Geocode city names to coordinates
    - Fetch tourist attractions from Geoapify
    - Retrieve indoor and outdoor activity venues

Key Dependencies:
    - requests: For HTTP API calls
    - geopy: For location geocoding
    - tools.decorator: For @tool registration

External APIs:
    - Geoapify Places API: Location-based venue discovery
    - Nominatim (via geopy): Geocoding service
"""

import requests

from typing import TypedDict, List
from geopy.geocoders import Nominatim
from tools.decorator import tool


class CityAttractionsOutput(TypedDict):
    """
    Structured output for city attractions.
    
    Attributes:
        city: Name of the queried city.
        attractions: List of tourist attraction names.
    """
    city: str
    attractions: List[str]


class ActivitiesOutput(TypedDict):
    """
    Structured output for city activities.
    
    Attributes:
        city: Name of the queried city.
        activity_type: Type of activities ("indoor" or "outdoor").
        activities: List of activity/venue names.
    """
    city: str
    activity_type: str
    activities: List[str]


@tool(
    name="get_city_attractions",
    description="Get a list of popular tourist attractions in a given city.",
    category="travel"
)
def get_city_attractions(city: str, limit: int = 10) -> CityAttractionsOutput:
    """
    Retrieve popular tourist attractions in a city.
    
    Geocodes the city name and queries Geoapify for tourism sights
    within proximity of the city center.
    
    Args:
        city: Name of the city to search.
        limit: Maximum number of attractions to return (default: 10).
        
    Returns:
        CityAttractionsOutput with city name and list of attractions.
        Returns error dict if request fails.
    """
    try:
        # Geocode city name to coordinates
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(city)
        
        lat = location.latitude
        lon = location.longitude

        # Query Geoapify Places API for tourism sights
        categories = "tourism.sights"
        attractions_url = f"https://api.geoapify.com/v2/places?categories={categories}&bias=proximity:{lon},{lat}&limit={limit}&apiKey=960f23468e46413b90c52f435dc8b1de"
        attractions_response = requests.get(attractions_url, timeout=10)
        attractions_response.raise_for_status()
        attractions_data = attractions_response.json()

        # Extract unique attraction names from response
        attractions = set()
        for feature in attractions_data.get('features', []):
            name = feature['properties'].get('name', None)
            if name:
                attractions.add(name)
        
        return CityAttractionsOutput(city=city, attractions=list(attractions))
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_indoor_activities",
    description="Get a list of indoor activities and venues in a given city (museums, theaters, shopping malls, etc.).",
    category="travel"
)
def get_indoor_activities(city: str, limit: int = 10) -> ActivitiesOutput:
    """
    Retrieve indoor activity venues in a city.
    
    Searches for museums, cultural venues, arcades, aquariums,
    cinemas, and shopping malls near the city center.
    
    Args:
        city: Name of the city to search.
        limit: Maximum number of venues to return (default: 10).
        
    Returns:
        ActivitiesOutput with city, type "indoor", and venue list.
        Returns error dict if request fails.
    """
    try:
        # Geocode city name to coordinates
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(city)
        
        lat = location.latitude
        lon = location.longitude

        # Query Geoapify for indoor entertainment and commercial venues
        categories = "entertainment.museum,entertainment.culture,entertainment.amusement_arcade,entertainment.aquarium,entertainment.cinema,commercial.shopping_mall"
        activities_url = f"https://api.geoapify.com/v2/places?categories={categories}&bias=proximity:{lon},{lat}&limit={limit}&apiKey=960f23468e46413b90c52f435dc8b1de"
        activities_response = requests.get(activities_url, timeout=10)
        activities_response.raise_for_status()
        activities_data = activities_response.json()

        # Extract unique venue names from response
        activities = set()
        for feature in activities_data.get('features', []):
            name = feature['properties'].get('name', None)
            if name:
                activities.add(name)
        
        return ActivitiesOutput(city=city, activity_type="indoor", activities=list(activities))
    except Exception as e:
        return {"error": str(e)}


@tool(
    name="get_outdoor_activities",
    description="Get a list of outdoor activities and venues in a given city (parks, hiking trails, sports facilities, etc.).",
    category="travel"
)
def get_outdoor_activities(city: str, limit: int = 10) -> ActivitiesOutput:
    """
    Retrieve outdoor activity venues in a city.
    
    Searches for parks, trails, beaches, sports facilities,
    camping areas, and ski resorts near the city center.
    
    Args:
        city: Name of the city to search.
        limit: Maximum number of venues to return (default: 10).
        
    Returns:
        ActivitiesOutput with city, type "outdoor", and venue list.
        Returns error dict if request fails.
    """
    try:
        # Geocode city name to coordinates
        geolocator = Nominatim(user_agent="ai-workflows")
        location = geolocator.geocode(city)
        
        lat = location.latitude
        lon = location.longitude

        # Query Geoapify for outdoor and recreational venues
        categories = "leisure,highway,natural,national_park,camping,beach,sport,ski,commercial.outdoor_and_sport"
        activities_url = f"https://api.geoapify.com/v2/places?categories={categories}&bias=proximity:{lon},{lat}&limit={limit}&apiKey=960f23468e46413b90c52f435dc8b1de"
        activities_response = requests.get(activities_url, timeout=10)
        activities_response.raise_for_status()
        activities_data = activities_response.json()

        # Extract unique venue names from response
        activities = set()
        for feature in activities_data.get('features', []):
            name = feature['properties'].get('name', None)
            if name:
                activities.add(name)
        
        return ActivitiesOutput(city=city, activity_type="outdoor", activities=list(activities))
    except Exception as e:
        return {"error": str(e)}