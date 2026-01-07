from tools.decorator import tool
from tools.weather import get_weather, WeatherOutput
from tools.travel import get_indoor_activities, get_outdoor_activities, ActivitiesOutput

@tool(
    name="check_weather_and_plan_activities", 
    description="Get the weather forecast for a given location and number of days, and plan activities accordingly.",    
    category="planning"
)
def check_weather_and_plan_activities(location: str, forecast_days: int = 7) -> ActivitiesOutput: 
    try:
        weather_data: WeatherOutput = get_weather(location, forecast_days)
        will_rain = any("rain" in forecast.split(" ") for forecast in weather_data.get("forecasts", []))
        return get_indoor_activities(location) if will_rain else get_outdoor_activities(location)
    except Exception as e:
        return {"error": str(e)}
