import yaml
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "config.yaml"

def load_config(config_path:Path = DEFAULT_CONFIG) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    return config
