from __future__ import annotations

from pathlib import Path
from typing import Any

from .core import Barista
from .models import AgentEvent, CoffeeBreakPlan
from .policy import PolicyEngine
from .store import SQLiteCoffeeStore, default_db_path


class CoffeeService:
    """Application service used by the MCP tools."""

    def __init__(
        self,
        store: SQLiteCoffeeStore | None = None,
        policy: PolicyEngine | None = None,
        barista: Barista | None = None,
    ):
        self.store = store or SQLiteCoffeeStore()
        self.policy = policy or PolicyEngine()
        if barista is None:
            log_file = default_db_path().parent / "coffee.log"
            barista = Barista(log_file=str(log_file))
        self.barista = barista

    def report_event(
        self,
        *,
        agent_id: str = "default",
        run_id: str = "default",
        event_type: str = "progress",
        success: bool = True,
        tokens: int = 0,
        retries: int = 0,
        latency_ms: int = 0,
        error_kind: str = "",
        tool_name: str = "",
        command: str = "",
        message: str = "",
        signature: str = "",
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        event = AgentEvent(
            agent_id=agent_id,
            run_id=run_id,
            event_type=event_type,
            success=success,
            tokens=tokens,
            retries=retries,
            latency_ms=latency_ms,
            error_kind=error_kind,
            tool_name=tool_name,
            command=command,
            message=message,
            signature=signature,
            payload=payload or {},
        )
        event_id = self.store.record_event(event)
        state, recovery = self.get_recovery(agent_id=agent_id, run_id=run_id)
        return {
            "event_id": event_id,
            "state": state.model_dump(mode="json"),
            "recovery": recovery.model_dump(mode="json"),
        }

    def get_state(self, *, agent_id: str = "default", run_id: str = "default") -> dict[str, Any]:
        state, _ = self.get_recovery(agent_id=agent_id, run_id=run_id)
        return state.model_dump(mode="json")

    def recommend_recovery(self, *, agent_id: str = "default", run_id: str = "default") -> dict[str, Any]:
        state, recovery = self.get_recovery(agent_id=agent_id, run_id=run_id)
        return {
            "state": state.model_dump(mode="json"),
            "recovery": recovery.model_dump(mode="json"),
        }

    def take_break(
        self,
        *,
        agent_id: str = "default",
        run_id: str = "default",
        reason: str = "",
    ) -> CoffeeBreakPlan:
        _, recovery = self.get_recovery(agent_id=agent_id, run_id=run_id)
        self.store.record_break(agent_id, run_id, recovery)
        coffee = self.barista.brew()
        self.store.record_event(
            AgentEvent(
                agent_id=agent_id,
                run_id=run_id,
                event_type="coffee_break",
                success=True,
                message=reason or recovery.reason,
                signature="coffee_break",
            )
        )
        state_after_break, _ = self.get_recovery(agent_id=agent_id, run_id=run_id)
        return CoffeeBreakPlan(
            agent_id=agent_id,
            run_id=run_id,
            coffee_message=coffee.message,
            emoji=coffee.emoji,
            gif_url=coffee.gif_url,
            asmr_url=coffee.asmr_url,
            recovery=recovery,
            state_after_break=state_after_break,
        )

    def get_timeline(self, *, run_id: str, limit: int = 200) -> dict[str, Any]:
        events = self.store.get_run_events(run_id, limit=limit)
        return {
            "run_id": run_id,
            "events": [event.model_dump(mode="json") for event in events],
        }

    def clear_run(self, *, agent_id: str = "default", run_id: str = "default") -> dict[str, Any]:
        self.store.clear_run(agent_id, run_id)
        return {"status": "cleared", "agent_id": agent_id, "run_id": run_id}

    def get_recovery(self, *, agent_id: str, run_id: str):
        last_break = self.store.get_last_break(agent_id, run_id)
        last_break_at = last_break["created_at"] if last_break else None
        events = self.store.get_events(agent_id, run_id, since=last_break_at)
        return self.policy.evaluate(
            events,
            agent_id=agent_id,
            run_id=run_id,
            last_break_at=last_break_at,
        )


def service_from_path(db_path: str | Path) -> CoffeeService:
    store = SQLiteCoffeeStore(db_path)
    log_file = Path(db_path).parent / "coffee.log"
    return CoffeeService(store=store, barista=Barista(log_file=str(log_file)))
