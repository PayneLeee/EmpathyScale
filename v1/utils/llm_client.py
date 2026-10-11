import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config.json"


def load_api_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load API configuration from config.json and environment variables."""
    config_file = Path(config_path).resolve() if config_path else DEFAULT_CONFIG_PATH
    config: Dict[str, Any] = {}

    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception:
            config = {}

    env = os.environ
    if env.get("OPENAI_API_KEY"):
        config["openai_api_key"] = env["OPENAI_API_KEY"]
    elif env.get("OPENAI_KEY"):
        config["openai_api_key"] = env["OPENAI_KEY"]
    elif env.get("API_KEY"):
        config["openai_api_key"] = env["API_KEY"]

    if env.get("OPENAI_BASE_URL"):
        config["openai_base_url"] = env["OPENAI_BASE_URL"]
    elif env.get("OPENAI_API_BASE"):
        config["openai_base_url"] = env["OPENAI_API_BASE"]
    elif env.get("OPENAI_URL"):
        config["openai_base_url"] = env["OPENAI_URL"]

    if env.get("MODEL_NAME"):
        config["model_name"] = env["MODEL_NAME"]
    elif env.get("OPENAI_MODEL"):
        config["model_name"] = env["OPENAI_MODEL"]

    return config


def get_api_key(config_path: Optional[str] = None) -> Optional[str]:
    config = load_api_config(config_path)
    return config.get("openai_api_key")


def get_api_base_url(config_path: Optional[str] = None) -> Optional[str]:
    config = load_api_config(config_path)
    return config.get("openai_base_url")


def get_default_model_name(config_path: Optional[str] = None) -> str:
    config = load_api_config(config_path)
    return config.get("model_name", "deepseek-v4-pro")


def create_llm(
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
    model: Optional[str] = None,
    temperature: float = 0.7,
    timeout: Optional[float] = None,
    openai_api_base: Optional[str] = None,
    base_url: Optional[str] = None,
    config_path: Optional[str] = None,
    **kwargs: Any,
) -> ChatOpenAI:
    """Create a configured ChatOpenAI instance from centralized settings."""
    config = load_api_config(config_path)

    actual_api_key = api_key or config.get("openai_api_key")
    if not actual_api_key:
        raise ValueError(
            "OpenAI API key is required. Set OPENAI_API_KEY in environment or openai_api_key in config.json"
        )

    actual_model_name = model_name or model or config.get("model_name") or "deepseek-v4-pro"
    actual_openai_api_base = openai_api_base or base_url or config.get("openai_base_url")

    params: Dict[str, Any] = {
        "api_key": actual_api_key,
        "model_name": actual_model_name,
        "temperature": temperature,
        **kwargs,
    }
    # Default a request timeout so a stalled upstream (e.g. a queued GLM request)
    # fails loudly instead of hanging the whole pipeline forever. Real runs showed
    # a 14-minute silent stall on the first call with timeout=None.
    effective_timeout = timeout if timeout is not None else 240
    params["timeout"] = effective_timeout
    if actual_openai_api_base:
        params["openai_api_base"] = actual_openai_api_base

    return ChatOpenAI(**params)
