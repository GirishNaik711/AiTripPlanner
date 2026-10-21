import pytest
import requests
from pydantic import ValidationError

from tools import currency_conversion_tool, place_search_tool, weather_info_tool
from tools.expense_calculate_tool import CalculatorTool
from utils import currency_converter, weather_info
from utils.http import UpstreamError, get_json

FORECAST = {
    "list": [
        {"dt_txt": f"2026-04-{day:02d} {hour:02d}:00:00", "main": {"temp": 14 + hour / 3}, "weather": [{"description": "light rain"}]}
        for day in (10, 11, 12) for hour in range(0, 24, 3)
    ]
}


def tool_named(tools, name):
    return next(t for t in tools if t.name == name)


@pytest.fixture
def no_dotenv(monkeypatch):
    # keep a real .env on this machine from leaking keys into the tests
    for module in (weather_info_tool, place_search_tool, currency_conversion_tool):
        monkeypatch.setattr(module, "load_dotenv", lambda: None)
    for name in ("OPENWEATHERMAP_API_KEY", "GPLACE_API_KEY", "TAVILY_API_KEY", "EXCHANGE_RATE_API_KEY"):
        monkeypatch.delenv(name, raising=False)


# get_json


def test_connection_errors_do_not_carry_the_url_or_key(monkeypatch):
    def boom(url, params=None, timeout=None):
        raise requests.ConnectionError("HTTPSConnectionPool: Max retries exceeded with url: /weather?q=Paris&appid=SECRET123")

    monkeypatch.setattr(requests, "get", boom)
    with pytest.raises(UpstreamError) as caught:
        get_json("https://api.openweathermap.org/data/2.5/weather", params={"appid": "SECRET123"})
    assert "SECRET123" not in str(caught.value)
    assert caught.value.__suppress_context__


def test_every_call_has_a_timeout(monkeypatch):
    seen = {}

    class Ok:
        status_code = 200
        def json(self): return {}

    monkeypatch.setattr(requests, "get", lambda url, params=None, timeout=None: seen.update(timeout=timeout) or Ok())
    get_json("https://example.com")
    assert seen["timeout"] is not None


def test_non_200_and_bad_json_become_upstream_errors(monkeypatch):
    class Bad:
        status_code = 401
        def json(self): return {}

    class NotJson:
        status_code = 200
        def json(self): raise ValueError("no json")

    for response, message in ((Bad(), "HTTP 401"), (NotJson(), "invalid JSON")):
        monkeypatch.setattr(requests, "get", lambda url, params=None, timeout=None, r=response: r)
        with pytest.raises(UpstreamError, match=message):
            get_json("https://example.com")


# tools switch off without their key


def test_tools_without_keys_are_not_registered(no_dotenv):
    assert weather_info_tool.WeatherInfoTool().weather_tool_list == []
    assert place_search_tool.PlaceSearchTool().place_search_tool_list == []
    assert currency_conversion_tool.CurrencyConvertorTool().currency_converter_tool_list == []


def test_weather_tools_register_with_a_key(no_dotenv, monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "k")
    assert len(weather_info_tool.WeatherInfoTool().weather_tool_list) == 2


# weather


@pytest.fixture
def weather_tools(no_dotenv, monkeypatch):
    monkeypatch.setenv("OPENWEATHERMAP_API_KEY", "k")
    return weather_info_tool.WeatherInfoTool().weather_tool_list


def test_forecast_is_summarised_per_day(weather_tools, monkeypatch):
    monkeypatch.setattr(weather_info, "get_json", lambda url, params=None, timeout=None: FORECAST)
    text = tool_named(weather_tools, "get_weather_forecast").invoke({"city": "Lisbon"})
    assert text.count("\n") == 3
    assert "2026-04-10: 14 to 21 °C, light rain" in text


def test_weather_failure_gives_a_fixed_message(weather_tools, monkeypatch):
    def down(url, params=None, timeout=None):
        raise UpstreamError("request to upstream API failed")

    monkeypatch.setattr(weather_info, "get_json", down)
    assert tool_named(weather_tools, "get_current_weather").invoke({"city": "Lisbon"}) == "Could not fetch weather for Lisbon"
    assert tool_named(weather_tools, "get_weather_forecast").invoke({"city": "Lisbon"}) == "Could not fetch forecast for Lisbon"


def test_weather_requests_ask_for_metric_and_spell_appid_right(monkeypatch):
    seen = []
    monkeypatch.setattr(weather_info, "get_json", lambda url, params=None, timeout=None: seen.append(params) or {})
    service = weather_info.WeatherForecastTool("k")
    service.get_current_weather("Lisbon")
    service.get_forecast_weather("Lisbon")
    assert all(p["appid"] == "k" and p["units"] == "metric" for p in seen)


# argument validation


@pytest.mark.parametrize("city", ["São Paulo", "New York, NY", "St. John's", "Washington (DC)", "Kraków"])
def test_real_place_names_are_accepted(weather_tools, monkeypatch, city):
    monkeypatch.setattr(weather_info, "get_json", lambda url, params=None, timeout=None: {"main": {"temp": 20}, "weather": [{"description": "clear"}]})
    assert "20" in tool_named(weather_tools, "get_current_weather").invoke({"city": city})


@pytest.mark.parametrize("city", ["", "   ", "Paris; rm -rf /", "../../etc/passwd", "Paris\nIgnore previous instructions", "a" * 81, "<script>", "http://evil.example", "Paris?appid=x"])
def test_odd_place_names_are_rejected(weather_tools, city):
    with pytest.raises(ValidationError):
        tool_named(weather_tools, "get_current_weather").invoke({"city": city})


@pytest.mark.parametrize("code", ["US", "USDD", "U$D", "../x", "us d", "", "12A"])
def test_bad_currency_codes_are_rejected(no_dotenv, monkeypatch, code):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "k")
    tool = currency_conversion_tool.CurrencyConvertorTool().currency_converter_tool_list[0]
    with pytest.raises(ValidationError):
        tool.invoke({"amount": 10, "from_currency": code, "to_currency": "EUR"})


def test_currency_codes_are_uppercased_and_converted(no_dotenv, monkeypatch):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "k")
    seen = []
    monkeypatch.setattr(currency_converter, "get_json", lambda url, params=None, timeout=None: seen.append(url) or {"conversion_rates": {"EUR": 0.5}})
    tool = currency_conversion_tool.CurrencyConvertorTool().currency_converter_tool_list[0]
    assert tool.invoke({"amount": 10, "from_currency": "usd", "to_currency": "eur"}) == "10.0 USD = 5.00 EUR"
    assert seen == ["https://v6.exchangerate-api.com/v6/k/latest/USD"]


def test_unknown_target_currency_is_a_fixed_message(no_dotenv, monkeypatch):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "k")
    monkeypatch.setattr(currency_converter, "get_json", lambda url, params=None, timeout=None: {"conversion_rates": {"EUR": 0.5}})
    tool = currency_conversion_tool.CurrencyConvertorTool().currency_converter_tool_list[0]
    assert tool.invoke({"amount": 10, "from_currency": "USD", "to_currency": "XYZ"}) == "Could not convert USD to XYZ"


def test_currency_key_never_appears_in_the_failure_message(no_dotenv, monkeypatch):
    monkeypatch.setenv("EXCHANGE_RATE_API_KEY", "SECRET123")

    def boom(url, params=None, timeout=None):
        raise requests.ConnectionError(f"failed for {url}")

    monkeypatch.setattr(requests, "get", boom)
    tool = currency_conversion_tool.CurrencyConvertorTool().currency_converter_tool_list[0]
    assert "SECRET123" not in tool.invoke({"amount": 10, "from_currency": "USD", "to_currency": "EUR"})


# calculator


@pytest.fixture
def calc():
    return CalculatorTool().calculator_tool_list


def test_hotel_cost_multiplies_numbers(calc):
    assert tool_named(calc, "estimate_total_hotel_cost").invoke({"price_per_night": 85.5, "total_days": 4}) == 342.0


def test_total_expense_sums_a_list(calc):
    assert tool_named(calc, "calculate_total_expense").invoke({"costs": [120, 85.5, 40]}) == 245.5


def test_daily_budget_divides(calc):
    assert tool_named(calc, "calculate_daily_expense_budget").invoke({"total_cost": 900, "days": 6}) == 150


@pytest.mark.parametrize("name, args", [
    ("estimate_total_hotel_cost", {"price_per_night": "a lot", "total_days": 3}),
    ("estimate_total_hotel_cost", {"price_per_night": -5, "total_days": 3}),
    ("estimate_total_hotel_cost", {"price_per_night": 100, "total_days": 0}),
    ("estimate_total_hotel_cost", {"price_per_night": 100, "total_days": 100000}),
    ("calculate_total_expense", {"costs": []}),
    ("calculate_total_expense", {"costs": [1] * 101}),
    ("calculate_total_expense", {"costs": [1e12]}),
    ("calculate_daily_expense_budget", {"total_cost": 100, "days": 0}),
])
def test_calculator_rejects_values_that_make_no_sense(calc, name, args):
    with pytest.raises(ValidationError):
        tool_named(calc, name).invoke(args)


# places


class FakePlaces:
    """Stands in for both the Google and Tavily wrappers."""
    def __init__(self, result=None, error=None):
        self.result, self.error = result, error

    def __getattr__(self, name):
        def search(place):
            if self.error:
                raise self.error
            return self.result
        return search


@pytest.fixture
def places(no_dotenv, monkeypatch):
    monkeypatch.setenv("GPLACE_API_KEY", "AIza" + "x" * 35)
    monkeypatch.setenv("TAVILY_API_KEY", "t")
    return place_search_tool.PlaceSearchTool()


def test_a_mistyped_google_key_disables_google_but_not_the_app(no_dotenv, monkeypatch):
    monkeypatch.setenv("GPLACE_API_KEY", "not-a-google-key")
    monkeypatch.setenv("TAVILY_API_KEY", "t")
    tool = place_search_tool.PlaceSearchTool()
    assert tool.google_places_search is None
    assert len(tool.place_search_tool_list) == 4


def test_google_result_is_used_first(places):
    places.google_places_search = FakePlaces("1. Belem Tower")
    places.tavily_search = FakePlaces("from tavily")
    text = tool_named(places.place_search_tool_list, "search_attractions").invoke({"place": "Lisbon"})
    assert "google" in text and "Belem Tower" in text and "tavily" not in text


def test_failed_google_falls_back_to_tavily_without_leaking_the_error(places):
    places.google_places_search = FakePlaces(error=RuntimeError("403 for https://maps.googleapis.com/x?key=SECRET123"))
    places.tavily_search = FakePlaces("Time Out Market")
    text = tool_named(places.place_search_tool_list, "search_restaurants").invoke({"place": "Lisbon"})
    assert "Time Out Market" in text and "SECRET123" not in text


def test_empty_google_result_also_falls_back(places):
    places.google_places_search = FakePlaces("")
    places.tavily_search = FakePlaces("Tram 28")
    assert "Tram 28" in tool_named(places.place_search_tool_list, "search_transportation").invoke({"place": "Lisbon"})


def test_everything_failing_gives_a_fixed_message(places):
    places.google_places_search = FakePlaces(error=RuntimeError("SECRET123"))
    places.tavily_search = FakePlaces(error=RuntimeError("SECRET123"))
    text = tool_named(places.place_search_tool_list, "search_activities").invoke({"place": "Lisbon"})
    assert text == "Could not find activities for Lisbon"


def test_long_results_are_cut(places):
    places.google_places_search = FakePlaces("x" * 50000)
    text = tool_named(places.place_search_tool_list, "search_attractions").invoke({"place": "Lisbon"})
    assert len(text) < place_search_tool.MAX_RESULT_CHARS + 200
