import os
import logging
from typing import Literal, Optional, Any
from pydantic import BaseModel, ConfigDict, Field
from utils.config_loader import load_config
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

LLM_TIMEOUT = 30
LLM_MAX_RETRIES = 2


class ConfigLoader:
    def __init__(self):
        logger.debug("loading config")
        self.config = load_config()

    def __getitem__(self, key):
        return self.config[key]

class ModelLoader(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_provider :Literal["groq", "openai"] = "groq"
    config: Optional[ConfigLoader] = Field(default=None, exclude=True)

    def model_post_init(self, __context:Any) -> None:
        self.config = ConfigLoader()

    def load_llm(self, model_key: str = "model_name", max_tokens: int = 2048, temperature: float = 0.3):
        """
        Load and return the LLM. model_key picks an entry under llm.<provider> in config.yaml.
        """

        logger.info("Loading %s model (%s)", self.model_provider, model_key)

        env_name = "GROQ_API_KEY" if self.model_provider == "groq" else "OPENAI_API_KEY"
        api_key = os.getenv(env_name)
        if not api_key:
            raise RuntimeError(f"{env_name} is not set")

        model_name = self.config["llm"][self.model_provider][model_key]
        if self.model_provider == "groq":
            return ChatGroq(model=model_name, api_key=api_key, temperature=temperature, max_tokens=max_tokens,
                            timeout=LLM_TIMEOUT, max_retries=LLM_MAX_RETRIES)
        return ChatOpenAI(model=model_name, api_key=api_key, timeout=LLM_TIMEOUT, max_retries=LLM_MAX_RETRIES)
