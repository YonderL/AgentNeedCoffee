from typing import Any, Dict
from ..core import EmotionMonitor, Barista

def get_coffee_break_tool_schema() -> Dict[str, Any]:
    """Returns the JSON schema for OpenAI function calling."""
    return {
        "type": "function",
        "function": {
            "name": "take_coffee_break",
            "description": "Trigger a virtual coffee break to reset fatigue and irritation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "The reason for taking a break (e.g., high fatigue)."
                    }
                },
                "required": ["reason"]
            }
        }
    }

def handle_coffee_break(args: Dict[str, Any]) -> str:
    """Executes the coffee break logic."""
    monitor = EmotionMonitor()
    barista = Barista()
    
    # In a real app, this would check if it really needs it
    # But function calling implies the model decided to call it.
    coffee = barista.brew()
    monitor.consume_coffee()
    
    return f"☕️ Break processed: {coffee.message}. Fatigue reset."
