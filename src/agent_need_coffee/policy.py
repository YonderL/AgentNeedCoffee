from __future__ import annotations

from collections import Counter
from datetime import datetime

from .models import AgentEvent, AgentState, RecoveryAction


ERROR_EVENT_TYPES = {
    "tool_error",
    "test_failure",
    "model_error",
    "rate_limit",
    "retry",
    "context_pressure",
}


class PolicyEngine:
    """Turns recent agent events into a concrete recovery action."""

    def __init__(self, token_soft_limit: int = 80_000, token_hard_limit: int = 160_000):
        self.token_soft_limit = token_soft_limit
        self.token_hard_limit = token_hard_limit

    def evaluate(
        self,
        events: list[AgentEvent],
        *,
        agent_id: str,
        run_id: str,
        last_break_at: str | None = None,
    ) -> tuple[AgentState, RecoveryAction]:
        state = self._state_from_events(events, agent_id, run_id, last_break_at)
        return state, self._recommend(state)

    def _state_from_events(
        self,
        events: list[AgentEvent],
        agent_id: str,
        run_id: str,
        last_break_at: str | None,
    ) -> AgentState:
        if not events:
            return AgentState(agent_id=agent_id, run_id=run_id, last_break_at=last_break_at)

        failure_events = [event for event in events if self._is_failure(event)]
        success_events = [event for event in events if event.success and event.event_type not in ERROR_EVENT_TYPES]
        retry_count = sum(event.retries for event in events) + sum(
            1 for event in events if event.event_type == "retry"
        )
        total_tokens = sum(event.tokens for event in events)
        rate_limit_events = sum(
            1
            for event in events
            if event.event_type == "rate_limit" or "rate" in event.error_kind.lower()
        )
        context_pressure_events = sum(
            1
            for event in events
            if event.event_type == "context_pressure" or event.tokens >= self.token_soft_limit
        )

        signatures = [event.loop_signature() for event in failure_events]
        signature_counts = Counter(signatures)
        dominant_signature, repeated_failure_count = ("", 0)
        if signature_counts:
            dominant_signature, repeated_failure_count = signature_counts.most_common(1)[0]

        duration_seconds = self._duration_seconds(events)
        fatigue_score = min(
            1.0,
            (total_tokens / max(self.token_hard_limit, 1)) * 0.55
            + (retry_count / 12) * 0.25
            + (duration_seconds / 7200) * 0.20,
        )
        friction_score = min(
            1.0,
            (len(failure_events) / 8) * 0.45
            + (repeated_failure_count / 5) * 0.40
            + (rate_limit_events / 3) * 0.15,
        )
        loop_score = min(1.0, repeated_failure_count / 5)

        status = "steady"
        if loop_score >= 1.0 or (len(failure_events) >= 6 and not success_events):
            status = "blocked"
        elif repeated_failure_count >= 3 or friction_score >= 0.65:
            status = "stuck"
        elif fatigue_score >= 0.55 or friction_score >= 0.35:
            status = "strained"

        return AgentState(
            agent_id=agent_id,
            run_id=run_id,
            active_since=events[0].created_at,
            last_event_at=events[-1].created_at,
            last_break_at=last_break_at,
            total_events=len(events),
            failure_events=len(failure_events),
            success_events=len(success_events),
            retry_count=retry_count,
            total_tokens=total_tokens,
            repeated_failure_count=repeated_failure_count,
            dominant_failure_signature=dominant_signature,
            rate_limit_events=rate_limit_events,
            context_pressure_events=context_pressure_events,
            fatigue_score=round(fatigue_score, 3),
            friction_score=round(friction_score, 3),
            loop_score=round(loop_score, 3),
            status=status,
        )

    def _recommend(self, state: AgentState) -> RecoveryAction:
        if state.total_events == 0:
            return self._action(
                "low",
                "continue",
                "No runtime events have been reported for this run yet.",
                "Continue normally and report tool/model events as they happen.",
                state,
            )

        if state.repeated_failure_count >= 5 or state.status == "blocked":
            return self._action(
                "critical",
                "ask_human",
                "The same failure pattern is repeating and the run is unlikely to recover by brute force.",
                "Stop the loop, summarize the repeated failure, and ask for human guidance or a narrower target.",
                state,
                cooldown_seconds=0,
                next_steps=[
                    "Do not run the same failing command again unchanged.",
                    "Create a checkpoint containing goal, attempts, evidence, and the exact repeated signature.",
                    "Ask the user to choose between narrowing scope, changing approach, or stopping.",
                ],
            )

        if state.repeated_failure_count >= 3 or (state.failure_events >= 4 and state.success_events == 0):
            return self._action(
                "high",
                "create_checkpoint",
                "The agent appears stuck in a failure loop.",
                "Create a compact checkpoint, then choose one smaller verification step before continuing.",
                state,
                next_steps=[
                    "Summarize what has been tried in chronological order.",
                    "Name the smallest unverified assumption.",
                    "Run only one targeted check before making more edits.",
                ],
            )

        if state.context_pressure_events > 0 or state.total_tokens >= self.token_soft_limit:
            return self._action(
                "high",
                "compact_context",
                "The run is under context pressure.",
                "Compact the working context into a short state summary before continuing.",
                state,
                next_steps=[
                    "Keep current goal, decisions, changed files, commands, and next action.",
                    "Drop stale logs and duplicate traces.",
                    "Resume from the compacted checkpoint.",
                ],
            )

        if state.rate_limit_events > 0 or state.retry_count >= 3:
            return self._action(
                "medium",
                "backoff",
                "Retries or rate-limit events are accumulating.",
                "Pause briefly, reduce request/tool frequency, and retry with one changed variable.",
                state,
                cooldown_seconds=60,
                next_steps=[
                    "Wait for the cooldown before retrying external services.",
                    "Retry once with a smaller request or clearer input.",
                    "If it fails again, create a checkpoint instead of continuing retries.",
                ],
            )

        if state.failure_events >= 2:
            return self._action(
                "medium",
                "continue_with_smaller_step",
                "There are multiple failures, but no strong loop signature yet.",
                "Continue with a narrower diagnostic step.",
                state,
                next_steps=[
                    "State the next hypothesis before acting.",
                    "Choose a command or edit that tests only that hypothesis.",
                ],
            )

        return self._action(
            "low",
            "continue",
            "The run is steady.",
            "Continue normally.",
            state,
        )

    def _action(
        self,
        severity: str,
        action: str,
        reason: str,
        suggested_next_step: str,
        state: AgentState,
        *,
        cooldown_seconds: int = 0,
        next_steps: list[str] | None = None,
    ) -> RecoveryAction:
        checkpoint_prompt = (
            "Create an AgentNeedCoffee checkpoint with: current goal, relevant files, "
            "last successful evidence, failed attempts, dominant failure signature "
            f"({state.dominant_failure_signature or 'none'}), and one smallest next step."
        )
        return RecoveryAction(
            severity=severity,  # type: ignore[arg-type]
            action=action,  # type: ignore[arg-type]
            reason=reason,
            cooldown_seconds=cooldown_seconds,
            suggested_next_step=suggested_next_step,
            checkpoint_prompt=checkpoint_prompt,
            next_steps=next_steps or [],
        )

    def _is_failure(self, event: AgentEvent) -> bool:
        if event.event_type in ERROR_EVENT_TYPES:
            return True
        return not event.success

    def _duration_seconds(self, events: list[AgentEvent]) -> float:
        if len(events) < 2:
            return 0.0
        try:
            start = datetime.fromisoformat(events[0].created_at)
            end = datetime.fromisoformat(events[-1].created_at)
        except ValueError:
            return 0.0
        return max(0.0, (end - start).total_seconds())
