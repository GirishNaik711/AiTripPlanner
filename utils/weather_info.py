from utils.http import get_json

class WeatherForecastTool:
    def __init__(self, api_key:str):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"

    def get_current_weather(self, place:str):
        """Get current weather of a place"""
        params = {"q": place, "appid": self.api_key, "units": "metric"}
        return get_json(f"{self.base_url}/weather", params=params)

    def get_forecast_weather(self, place:str):
        """Get a weather forecast of a place"""
        params = {"q": place, "appid": self.api_key, "units": "metric"}
        return get_json(f"{self.base_url}/forecast", params=params)
