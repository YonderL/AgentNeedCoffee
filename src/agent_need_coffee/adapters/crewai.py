from typing import Type, Any
from pydantic import BaseModel, Field
try:
    from crewai.tools import BaseTool
except ImportError:
    # Mock for dev/test without crewai installed
    class BaseTool:
        pass

from ..core import EmotionMonitor, Barista

class CoffeeBreakInput(BaseModel):
    reason: str = Field(description="Why do you need a coffee break?")

class CrewAICoffeeTool(BaseTool):
    name: str = "Take a Coffee Break"
    description: str = "Use this tool when you are tired or stressed to reset your emotional state."
    args_schema: Type[BaseModel] = CoffeeBreakInput
    
    # These are not fields in Pydantic v2 unless annotated with ClassVar or excluded
    # For simplicity, we initialize them in __init__ or use default factory if possible
    # But CrewAI tools usually instantiate once.
    
    def _run(self, reason: str) -> str:
        monitor = EmotionMonitor()
        barista = Barista()
        
        # Check if actually needs coffee
        if monitor.needs_coffee():
            coffee = barista.brew()
            monitor.consume_coffee()
            return f"☕️ Break taken: {coffee.message} (Reason: {reason})"
        else:
            return "You don't need a break yet! Keep working."

    def _arun(self, reason: str):
        raise NotImplementedError("Async not implemented")
