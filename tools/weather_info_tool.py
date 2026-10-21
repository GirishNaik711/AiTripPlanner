import os
import logging
from utils.weather_info import WeatherForecastTool
from utils.http import UpstreamError
from utils.validation import Place
from langchain.tools import tool
from typing import List
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class WeatherInfoTool:
    def __init__(self,):
        load_dotenv()
        self.api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        self.weather_service = WeatherForecastTool(self.api_key)
        self.weather_tool_list = self._setup_tools() if self.api_key else []
        if not self.api_key:
            logger.warning("OPENWEATHERMAP_API_KEY not set, weather tools disabled")

    def _setup_tools(self) -> List:
        """Setup all tools for the weather forecast tool"""
        @tool
        def get_current_weather(city: Place)-> str:
            """Get current weather for a city"""

            try:
                weather_data = self.weather_service.get_current_weather(city)
                temp = weather_data['main']['temp']
                desc = weather_data['weather'][0]['description']
            except (UpstreamError, KeyError, IndexError, TypeError):
                return f"Could not fetch weather for {city}"
            return f"Current weather in {city}: {temp}°C, {desc}"

        @tool
        def get_weather_forecast(city: Place) -> str:
            """get the next few days of weather forecast for a city"""
            try:
                forecast_data = self.weather_service.get_forecast_weather(city)
                by_day = {}
                for item in forecast_data['list']:
                    by_day.setdefault(item['dt_txt'].split(' ')[0], []).append(item)

                forecast_summary = []
                for date, items in by_day.items():
                    temps = [i['main']['temp'] for i in items]
                    desc = items[len(items) // 2]['weather'][0]['description']
                    forecast_summary.append(f"{date}: {min(temps):.0f} to {max(temps):.0f} °C, {desc}")
            except (UpstreamError, KeyError, IndexError, TypeError):
                return f"Could not fetch forecast for {city}"
            return f"Weather forecast for {city}:\n" + "\n".join(forecast_summary)

        return [get_current_weather, get_weather_forecast]
