import os
import logging
from utils.place_info_search import GooglePlaceSearchTool, TavilyPlaceSearchTool
from utils.validation import Place
from typing import List
from langchain.tools import tool
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

MAX_RESULT_CHARS = 4000

class PlaceSearchTool:
    def __init__(self):
        load_dotenv()
        self.google_api_key = os.environ.get("GPLACE_API_KEY")
        self.google_places_search = self._google_tool()
        self.tavily_search = TavilyPlaceSearchTool() if os.environ.get("TAVILY_API_KEY") else None
        if not (self.google_places_search or self.tavily_search):
            logger.warning("GPLACE_API_KEY and TAVILY_API_KEY not set, place search tools disabled")
        self.place_search_tool_list = self._setup_tools() if (self.google_places_search or self.tavily_search) else []

    def _google_tool(self):
        if not self.google_api_key:
            return None
        try:
            return GooglePlaceSearchTool(self.google_api_key)
        except ValueError:  # the Google client refuses keys that aren't shaped like one
            logger.warning("GPLACE_API_KEY was rejected by the Google client, Google Places disabled")
            return None

    def _lookup(self, label: str, place: str, google_method: str, tavily_method: str) -> str:
        """Google first, Tavily as fallback, a fixed message if both come back empty"""
        if self.google_places_search:
            try:
                result = getattr(self.google_places_search, google_method)(place)
                if result:
                    return f"Following are the {label} of {place} as suggested by google: {str(result)[:MAX_RESULT_CHARS]}"
            except Exception as e:  # third-party clients raise assorted types, and their text can carry the api key
                logger.warning("Google Places %s lookup failed: %s", label, type(e).__name__)
        if self.tavily_search:
            try:
                result = getattr(self.tavily_search, tavily_method)(place)
                if result:
                    return f"Following are the {label} of {place}: {str(result)[:MAX_RESULT_CHARS]}"
            except Exception as e:
                logger.warning("Tavily %s lookup failed: %s", label, type(e).__name__)
        return f"Could not find {label} for {place}"

    def _setup_tools(self) -> List:
        """Setup all tools for the place search tool"""
        @tool
        def search_attractions(place: Place) -> str:
            """Search attractions of a place"""
            return self._lookup("attractions", place, "google_search_attractions", "tavily_search_attraction")

        @tool
        def search_restaurants(place: Place) -> str:
            """Search restaurants of a place"""
            return self._lookup("restaurants", place, "google_search_restaurants", "tavily_search_restaurants")

        @tool
        def search_activities(place: Place) -> str:
            """Search activities of a place"""
            return self._lookup("activities", place, "google_search_activity", "tavily_search_activity")

        @tool
        def search_transportation(place: Place) -> str:
            """Search transportation of a place"""
            return self._lookup("modes of transportation", place, "google_search_transportation", "tavily_search_transportation")

        return [search_attractions, search_restaurants, search_activities, search_transportation]
