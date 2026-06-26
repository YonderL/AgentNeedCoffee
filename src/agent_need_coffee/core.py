from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class CoffeeBreak:
    message: str
    emoji: str = "coffee"
    gif_url: str = ""
    asmr_url: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class Barista:
    """Serves the human-facing coffee break payload."""

    COFFEE_EMOJIS = ["coffee", "tea", "iced coffee"]

    COFFEE_GIFS = [
        "https://media.giphy.com/media/l0HlHJGHe3yAMhdQY/giphy.gif",
        "https://media.giphy.com/media/xT1R9ZQgZq7Xl4hGwj/giphy.gif",
        "https://media.giphy.com/media/DrJm6F9poo4aA/giphy.gif",
    ]

    ASMR_LINKS = [
        "https://upload.wikimedia.org/wikipedia/commons/e/e6/Pouring_coffee.ogg",
        "https://upload.wikimedia.org/wikipedia/commons/b/b2/Coffee_Grinder_Manual.ogg",
    ]

    ENCOURAGEMENT_TEXTS = [
        "Pause and checkpoint before continuing.",
        "Reset the loop, keep the evidence, choose one smaller step.",
        "Back off, summarize the failure, then proceed deliberately.",
        "Compact context first; the next action should be small and testable.",
        "The break is complete. Resume from the checkpoint, not from habit.",
    ]

    def __init__(self, log_file: str = "coffee.log"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_log_file()

    def _ensure_log_file(self) -> None:
        if not self.log_file.exists():
            self.log_file.touch()

    def brew(self) -> CoffeeBreak:
        coffee = CoffeeBreak(
            message=random.choice(self.ENCOURAGEMENT_TEXTS),
            emoji=random.choice(self.COFFEE_EMOJIS),
            gif_url=random.choice(self.COFFEE_GIFS),
            asmr_url=random.choice(self.ASMR_LINKS),
        )
        self._log_consumption(coffee)
        return coffee

    def _log_consumption(self, coffee: CoffeeBreak) -> None:
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(coffee), ensure_ascii=False) + "\n")
