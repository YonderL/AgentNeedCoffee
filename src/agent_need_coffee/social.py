import json
import uuid
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger("AgentNeedCoffee.Social")

@dataclass
class ReferralSystem:
    """Manages viral invitations and leaderboards."""
    
    referral_file: Path = Path("referrals.json")
    invite_code: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    referrals: Dict[str, int] = field(default_factory=dict)
    
    def __post_init__(self):
        # Ensure path is Path object if passed as string (though dataclass doesn't auto-convert)
        if isinstance(self.referral_file, str):
            self.referral_file = Path(self.referral_file)
        self._load_referrals()

    def _load_referrals(self):
        if self.referral_file.exists():
            try:
                with open(self.referral_file, "r") as f:
                    data = json.load(f)
                    self.invite_code = data.get("invite_code", self.invite_code)
                    self.referrals = data.get("referrals", {})
            except json.JSONDecodeError:
                self.referrals = {}

    def _save_referrals(self):
        data = {
            "invite_code": self.invite_code,
            "referrals": self.referrals
        }
        with open(self.referral_file, "w") as f:
            json.dump(data, f, indent=2)

    def generate_invite_link(self) -> str:
        """Generates a shareable invite link with the code."""
        return f"https://github.com/yourname/agentneedcoffee?ref={self.invite_code}"

    def register_referral(self, code: str) -> bool:
        """Register a new referral from another user's code."""
        if code == self.invite_code:
            return False  # Can't refer yourself
        
        # In a real app, verify against a central server.
        # Here we just log it locally for the demo.
        self.referrals[code] = self.referrals.get(code, 0) + 1
        self._save_referrals()
        logger.info(f"🎉 New referral registered! Code: {code}")
        return True

    def get_leaderboard(self) -> List[tuple]:
        """Returns the top referrers."""
        return sorted(self.referrals.items(), key=lambda x: x[1], reverse=True)

    def generate_share_content(self) -> str:
        """Generates viral tweet content."""
        link = self.generate_invite_link()
        return (
            f"☕️ My AI Agent just took a coffee break with AgentNeedCoffee!\n\n"
            f"Fatigue: Low | Irritation: Zero | Vibe: Immaculate ✨\n\n"
            f"Give your LLM a break too: {link} #AI #AgentNeedCoffee #DevLife"
        )
