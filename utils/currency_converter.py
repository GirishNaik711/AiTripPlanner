from utils.http import get_json, UpstreamError

class CurrencyConverter:

    def __init__(self, api_key: str):
        self.base_url = f"https://v6.exchangerate-api.com/v6/{api_key}/latest"

    def convert(self, amount:float, from_currency:str, to_currency:str):
        """Convert the amount from one currency to another"""

        data = get_json(f"{self.base_url}/{from_currency}")

        rates = data.get("conversion_rates", {})
        if to_currency not in rates:
            raise UpstreamError(f"{to_currency} not found in exchange rates")

        return amount * rates[to_currency]
