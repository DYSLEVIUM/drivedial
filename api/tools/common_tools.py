from typing import Any, Dict


def end_call_handler(name: str, arguments: Dict) -> Any:
    return {"status": "ending", "reason": arguments.get("reason", "user_request")}


def transfer_to_agent_handler(name: str, arguments: Dict) -> Any:
    return {
        "status": "transferring",
        "reason": arguments.get("reason", "customer_escalation"),
        "query_type": arguments.get("query_type", "general"),
        "message": "Lead captured on high priority. Our agent will call back shortly."
    }
