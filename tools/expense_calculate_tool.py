from utils.expense_calculator import Calculator
from utils.validation import Money, Days, Costs
from typing import List
from langchain.tools import tool

class CalculatorTool:
    def __init__(self):
        self.calculator = Calculator()
        self.calculator_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the calculator tool"""
        @tool
        def estimate_total_hotel_cost(price_per_night: Money, total_days: Days) -> float:
            """Calculate total hotel cost"""
            return self.calculator.multiply(price_per_night, total_days)

        @tool
        def calculate_total_expense(costs: Costs) -> float:
            """Calculate total expense of the trip from a list of costs"""
            return self.calculator.calculate_total(*costs)

        @tool
        def calculate_daily_expense_budget(total_cost: Money, days: Days) -> float:
            """Calculate daily expense"""
            return self.calculator.calculate_daily_budget(total_cost, days)

        return [estimate_total_hotel_cost, calculate_total_expense, calculate_daily_expense_budget]
