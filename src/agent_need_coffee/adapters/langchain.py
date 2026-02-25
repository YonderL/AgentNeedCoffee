from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_core.tools import BaseTool
from ..core import EmotionMonitor, Barista

class EmotionCallbackHandler(BaseCallbackHandler):
    """LangChain callback handler to monitor agent emotions."""

    def __init__(self, monitor: EmotionMonitor):
        self.monitor = monitor

    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> Any:
        self.monitor.start_task()

    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> Any:
        # Calculate tokens if available (simplified)
        tokens = 0
        if response.llm_output and "token_usage" in response.llm_output:
            tokens = response.llm_output["token_usage"].get("total_tokens", 0)
        
        self.monitor.record_tokens(tokens)
        self.monitor.end_task(success=True)

    def on_llm_error(self, error: Exception, **kwargs: Any) -> Any:
        self.monitor.record_retry()
        self.monitor.end_task(success=False)

class CoffeeBreakTool(BaseTool):
    """Tool for agents to take a coffee break."""
    name: str = "take_coffee_break"
    description: str = "Use this tool when you feel tired or irritated to regain energy."
    barista: Barista = Barista()
    monitor: EmotionMonitor = EmotionMonitor()

    def _run(self, query: str = "") -> str:
        """Use the tool."""
        coffee = self.barista.brew()
        self.monitor.consume_coffee()
        return f"☕️ {coffee.message} (Fatigue reset. Irritation cleared.)"

    async def _arun(self, query: str = "") -> str:
        """Use the tool asynchronously."""
        return self._run(query)
