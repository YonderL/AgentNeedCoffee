from __future__ import annotations

import json
import sys
from functools import lru_cache
from typing import Any

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover - exercised only when installed without mcp.
    FastMCP = None  # type: ignore[assignment]

from .service import CoffeeService


SERVER_INSTRUCTIONS = """
AgentNeedCoffee monitors AI agent runtime health. Report model/tool/test events,
then ask for recovery recommendations when retries, repeated failures, context
pressure, or long-running work appear. Treat high/critical recommendations as
control-flow instructions: checkpoint, compact context, back off, or ask a human.
""".strip()


if FastMCP is not None:
    mcp = FastMCP("AgentNeedCoffee", instructions=SERVER_INSTRUCTIONS)
else:
    mcp = None


@lru_cache(maxsize=1)
def get_service() -> CoffeeService:
    return CoffeeService()


if mcp is not None:

    @mcp.tool()
    def coffee_report_event(
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
    ) -> dict[str, Any]:
        """Record an agent runtime event and return the updated recovery recommendation.

        Use this after model calls, tool calls, failed commands, test failures, retries,
        rate limits, or context pressure. Reuse signature for repeated attempts so the
        server can detect loops reliably.
        """

        return get_service().report_event(
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
        )

    @mcp.tool()
    def coffee_get_state(agent_id: str = "default", run_id: str = "default") -> dict[str, Any]:
        """Return current agent health state since the last coffee break/checkpoint."""

        return get_service().get_state(agent_id=agent_id, run_id=run_id)

    @mcp.tool()
    def coffee_recommend_recovery(agent_id: str = "default", run_id: str = "default") -> dict[str, Any]:
        """Return an actionable recovery recommendation for the current agent run."""

        return get_service().recommend_recovery(agent_id=agent_id, run_id=run_id)

    @mcp.tool()
    def coffee_take_break(
        agent_id: str = "default",
        run_id: str = "default",
        reason: str = "",
    ) -> dict[str, Any]:
        """Create a coffee checkpoint and reset active loop analysis for future events."""

        plan = get_service().take_break(agent_id=agent_id, run_id=run_id, reason=reason)
        return plan.model_dump(mode="json")

    @mcp.tool()
    def coffee_clear_run(agent_id: str = "default", run_id: str = "default") -> dict[str, Any]:
        """Clear local state for one agent run. Use only when intentionally starting over."""

        return get_service().clear_run(agent_id=agent_id, run_id=run_id)

    @mcp.resource("coffee://agents/{agent_id}/state")
    def coffee_agent_state(agent_id: str) -> str:
        """Read the default-run state for an agent."""

        return json.dumps(
            get_service().get_state(agent_id=agent_id, run_id="default"),
            ensure_ascii=False,
            indent=2,
        )

    @mcp.resource("coffee://runs/{run_id}/timeline")
    def coffee_run_timeline(run_id: str) -> str:
        """Read the event timeline for a run."""

        return json.dumps(get_service().get_timeline(run_id=run_id), ensure_ascii=False, indent=2)

    @mcp.prompt()
    def coffee_recovery_review(agent_id: str = "default", run_id: str = "default") -> str:
        """Generate a recovery review prompt for a stuck agent run."""

        recommendation = get_service().recommend_recovery(agent_id=agent_id, run_id=run_id)
        return (
            "Review this AI agent run before continuing.\n\n"
            f"State and recovery recommendation:\n{json.dumps(recommendation, ensure_ascii=False, indent=2)}\n\n"
            "Write a compact checkpoint with the current goal, evidence, failed attempts, "
            "dominant loop signature, and exactly one next action. Do not repeat a failing "
            "command unchanged."
        )


def main() -> None:
    if mcp is None:
        print(
            "AgentNeedCoffee MCP requires the 'mcp' package. Install with: pip install 'mcp>=1.27,<2'",
            file=sys.stderr,
        )
        raise SystemExit(1)
    mcp.run()


if __name__ == "__main__":
    main()
