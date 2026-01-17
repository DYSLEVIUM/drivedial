from typing import Any, Callable, Dict, Optional

_tool_handlers: Dict[str, Callable[[str, dict], Any]] = {}


def register_tool_handler(tool_name: str, handler: Callable[[str, dict], Any]) -> None:
    _tool_handlers[tool_name] = handler


def get_tool_handler(tool_name: str) -> Optional[Callable[[str, dict], Any]]:
    return _tool_handlers.get(tool_name)


def execute_tool(name: str, arguments: dict) -> Any:
    handler = get_tool_handler(name)
    if handler:
        return handler(name, arguments)
    return None
