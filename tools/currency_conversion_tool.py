from utils.currency_converter import CurrencyConverter
from utils.http import UpstreamError
from utils.validation import CurrencyCode, Money
from typing import List
from langchain.tools import tool
from dotenv import load_dotenv
import logging
import os

logger = logging.getLogger(__name__)

class CurrencyConvertorTool:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("EXCHANGE_RATE_API_KEY")
        self.currency_service = CurrencyConverter(self.api_key)
        self.currency_converter_tool_list = self._setup_tools() if self.api_key else []
        if not self.api_key:
            logger.warning("EXCHANGE_RATE_API_KEY not set, currency tool disabled")

    def _setup_tools(self)-> List:
        """Setup all tools for the currency converter tool"""
        @tool
        def convert_currency(amount: Money, from_currency: CurrencyCode, to_currency: CurrencyCode) -> str:
            """convert amount from one currency to another using 3 letter currency codes"""
            try:
                converted = self.currency_service.convert(amount, from_currency, to_currency)
            except UpstreamError:
                return f"Could not convert {from_currency} to {to_currency}"
            return f"{amount} {from_currency} = {converted:.2f} {to_currency}"

        return [convert_currency]
