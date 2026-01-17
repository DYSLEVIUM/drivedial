import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from django.conf import settings

_agent_config: Optional[Dict[str, Any]] = None


def load_agent_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    global _agent_config
    
    if _agent_config is not None:
        return _agent_config
    
    if config_path is None:
        config_path = os.getenv("AGENT_CONFIG_PATH")
    
    if not config_path:
        raise ValueError("AGENT_CONFIG_PATH environment variable must be set")
    
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Agent config file not found: {config_path}")
    
    with open(config_file, "r", encoding="utf-8") as f:
        _agent_config = json.load(f)
    
    return _agent_config


def get_agent_config() -> Dict[str, Any]:
    if _agent_config is None:
        try:
            return load_agent_config()
        except Exception as e:
            import warnings
            warnings.warn(f"Failed to load agent config, using defaults: {e}")
            return {
                "agent_type": "car_sales",
                "metadata": {"name": "Agent", "company": "Company", "gender": "female", "voice": "coral"},
                "system_prompt": "You are a sales agent. Help the customer.",
                "greeting_instruction": "Greet the customer warmly.",
                "filler_context": "sales agent",
                "intent_classification_prompt": "Classify the query: {transcript}",
                "tools": []
            }
    return _agent_config


def reload_agent_config() -> Dict[str, Any]:
    global _agent_config
    _agent_config = None
    return load_agent_config()
