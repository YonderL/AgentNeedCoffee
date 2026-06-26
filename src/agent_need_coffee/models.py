from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


Severity = Literal["low", "medium", "high", "critical"]
RecoveryKind = Literal[
    "continue",
    "continue_with_smaller_step",
    "backoff",
    "compact_context",
    "create_checkpoint",
    "ask_human",
    "stop_loop",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class AgentEvent(BaseModel):
    """A normalized event emitted by an AI agent run."""

    agent_id: str = Field(default="default", description="Stable agent name or instance id.")
    run_id: str = Field(default="default", description="Stable id for the current agent run.")
    event_type: str = Field(
        default="progress",
        description=(
            "Event kind, for example model_call, tool_call, tool_error, retry, "
            "test_failure, rate_limit, context_pressure, checkpoint, or coffee_break."
        ),
    )
    success: bool = Field(default=True, description="Whether this event represents forward progress.")
    tokens: int = Field(default=0, ge=0, description="Tokens consumed by this step, if known.")
    retries: int = Field(default=0, ge=0, description="Retry attempts represented by this event.")
    latency_ms: int = Field(default=0, ge=0, description="Step latency in milliseconds, if known.")
    error_kind: str = Field(default="", description="Short error category, if this event failed.")
    tool_name: str = Field(default="", description="Tool, command, or subsystem involved.")
    command: str = Field(default="", description="Command or operation signature, if relevant.")
    message: str = Field(default="", description="Short human-readable event summary.")
    signature: str = Field(
        default="",
        description="Stable loop signature. If empty, it is derived from error/tool/command/message.",
    )
    created_at: str = Field(default_factory=utc_now, description="UTC ISO timestamp.")
    payload: dict[str, Any] = Field(default_factory=dict, description="Additional client metadata.")

    def loop_signature(self) -> str:
        if self.signature:
            return self.signature

        parts = [
            self.error_kind.strip().lower(),
            self.tool_name.strip().lower(),
            self.command.strip().lower(),
            self.message.strip().lower()[:160],
        ]
        signature = "|".join(part for part in parts if part)
        return signature or self.event_type.strip().lower()


class AgentState(BaseModel):
    """Current health summary for an agent run."""

    agent_id: str
    run_id: str
    active_since: Optional[str] = None
    last_event_at: Optional[str] = None
    last_break_at: Optional[str] = None
    total_events: int = 0
    failure_events: int = 0
    success_events: int = 0
    retry_count: int = 0
    total_tokens: int = 0
    repeated_failure_count: int = 0
    dominant_failure_signature: str = ""
    rate_limit_events: int = 0
    context_pressure_events: int = 0
    fatigue_score: float = 0.0
    friction_score: float = 0.0
    loop_score: float = 0.0
    status: Literal["steady", "strained", "stuck", "blocked"] = "steady"


class RecoveryAction(BaseModel):
    """Actionable recovery instruction for the calling agent."""

    severity: Severity
    action: RecoveryKind
    reason: str
    cooldown_seconds: int = 0
    suggested_next_step: str
    checkpoint_prompt: str
    next_steps: list[str] = Field(default_factory=list)


class CoffeeBreakPlan(BaseModel):
    """Result of an explicit coffee break/checkpoint."""

    agent_id: str
    run_id: str
    coffee_message: str
    emoji: str
    gif_url: str = ""
    asmr_url: str = ""
    recovery: RecoveryAction
    state_after_break: AgentState
