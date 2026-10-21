import logging
from utils.models_loaders import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition
from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.expense_calculate_tool import CalculatorTool
from tools.currency_conversion_tool import CurrencyConvertorTool

logger = logging.getLogger(__name__)

def tool_error_message(error: Exception) -> str:
    # The model sees this text, and it can end up in the reply, so never pass the exception text through.
    logger.warning("tool call failed: %s", type(error).__name__)
    return "That tool call failed or had invalid arguments. Do not retry with the same arguments. Continue with what you know and say the data was unavailable."

class GraphBuilder():
    def __init__(self,model_provider: str = "groq"):
        self.model_loader = ModelLoader(model_provider=model_provider)
        self.llm = self.model_loader.load_llm()

        self.tools = []

        self.weather_tools = WeatherInfoTool()
        self.place_search_tools = PlaceSearchTool()
        self.calculator_tools = CalculatorTool()
        self.currency_converter_tools = CurrencyConvertorTool()

        self.tools.extend([* self.weather_tools.weather_tool_list,
                           * self.place_search_tools.place_search_tool_list,
                           * self.calculator_tools.calculator_tool_list,
                           * self.currency_converter_tools.currency_converter_tool_list])

        self.llm_with_tools = self.llm.bind_tools(tools=self.tools)

        self.graph = None

        self.system_prompt = SYSTEM_PROMPT


    def agent_function(self,state: MessagesState):
        """Main agent function"""
        user_question = state["messages"]
        input_question = [self.system_prompt] + user_question
        response = self.llm_with_tools.invoke(input_question)
        return {"messages": [response]}
    def build_graph(self):
        graph_builder=StateGraph(MessagesState)
        graph_builder.add_node("agent", self.agent_function)
        graph_builder.add_node("tools", ToolNode(tools=self.tools, handle_tool_errors=tool_error_message))
        graph_builder.add_edge(START,"agent")
        graph_builder.add_conditional_edges("agent",tools_condition)
        graph_builder.add_edge("tools","agent")
        self.graph = graph_builder.compile()
        return self.graph

    def __call__(self):
        return self.build_graph()
