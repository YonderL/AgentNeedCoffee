import time
import random
import logging
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentNeedCoffee")

@dataclass
class CoffeeBreak:
    message: str
    emoji: str = "☕️"
    gif_url: str = ""
    asmr_url: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class Barista:
    """The virtual barista that serves coffee."""
    
    COFFEE_EMOJIS = ["☕️", "🍵", "🧋", "🥤", "🧊☕️"]
    
    # Predefined assets (in a real app, fetch from an API or config)
    COFFEE_GIFS = [
        "https://media.giphy.com/media/3o7TKUM3IgJBX2as9G/giphy.gif",
        "https://media.giphy.com/media/l0HlHJGHe3yAMhdQY/giphy.gif", 
        "https://media.giphy.com/media/xT1R9ZQgZq7Xl4hGwj/giphy.gif"
    ]
    
    ASMR_LINKS = [
        "https://example.com/asmr/coffee_pour.mp3",
        "https://example.com/asmr/cafe_ambience.mp3",
        "https://example.com/asmr/keyboard_typing.mp3"
    ]
    
    ENCOURAGEMENT_TEXTS = [
        "Take a deep breath. You've got this.",
        "Refueling... Systems nominal.",
        "Even silicon needs a break sometimes.",
        "Here's a fresh cup of virtual java.",
        "Pause. Reflect. Compile."
    ]

    def __init__(self, log_file: str = "coffee.log"):
        self.log_file = Path(log_file)
        self._ensure_log_file()

    def _ensure_log_file(self):
        if not self.log_file.exists():
            self.log_file.touch()

    def brew(self) -> CoffeeBreak:
        """Brews a virtual coffee and logs it."""
        coffee = CoffeeBreak(
            message=random.choice(self.ENCOURAGEMENT_TEXTS),
            emoji=random.choice(self.COFFEE_EMOJIS),
            gif_url=random.choice(self.COFFEE_GIFS),
            asmr_url=random.choice(self.ASMR_LINKS)
        )
        self._log_consumption(coffee)
        return coffee

    def _log_consumption(self, coffee: CoffeeBreak):
        """Logs the coffee consumption to a local file."""
        entry = asdict(coffee)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
        logger.info(f"☕️ Coffee served: {coffee.message}")


class EmotionMonitor:
    """Monitors agent metrics to determine emotional state."""
    
    def __init__(self, 
                 fatigue_threshold: float = 0.8, 
                 irritation_threshold: float = 0.7):
        self.fatigue_threshold = fatigue_threshold
        self.irritation_threshold = irritation_threshold
        
        # State
        self.current_fatigue = 0.0
        self.current_irritation = 0.0
        
        # Metrics history
        self.task_start_time: Optional[float] = None
        self.retry_count = 0
        self.token_usage = 0

    def start_task(self):
        """Call when a task starts."""
        self.task_start_time = time.time()
        self.retry_count = 0
        # Reset slightly on new task? Or accumulate? 
        # For this plugin, maybe accumulate fatigue but reset irritation if task succeeds.
        
    def record_retry(self):
        """Call when a task fails and retries."""
        self.retry_count += 1
        self.current_irritation += 0.1  # Increment irritation
        self.current_fatigue += 0.05

    def record_tokens(self, count: int):
        """Record token usage."""
        self.token_usage += count
        # Arbitrary: 1000 tokens = 0.01 fatigue
        self.current_fatigue += (count / 10000.0)

    def end_task(self, success: bool = True):
        """Call when a task ends."""
        if self.task_start_time:
            duration = time.time() - self.task_start_time
            # Long tasks increase fatigue
            self.current_fatigue += (duration / 3600.0)  # 1 hour = +1.0 fatigue? Maybe too slow.
            # Let's say 5 minutes = 0.1 fatigue -> 300s / 3000 = 0.1
            self.current_fatigue += (duration / 3000.0)
            self.task_start_time = None

        if success:
            # Success reduces irritation significantly
            self.current_irritation = max(0.0, self.current_irritation - 0.5)
            # Success reduces fatigue slightly (morale boost)
            self.current_fatigue = max(0.0, self.current_fatigue - 0.1)
        else:
            # Failure increases irritation
            self.current_irritation += 0.2

    def needs_coffee(self) -> bool:
        """Check if the agent needs a coffee break."""
        return (self.current_fatigue >= self.fatigue_threshold or 
                self.current_irritation >= self.irritation_threshold)

    def consume_coffee(self):
        """Reset metrics after coffee."""
        self.current_fatigue = 0.0
        self.current_irritation = 0.0
