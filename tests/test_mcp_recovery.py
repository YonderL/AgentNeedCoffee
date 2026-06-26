from pathlib import Path

import pytest

from agent_need_coffee.service import service_from_path
from agent_need_coffee.store import SQLiteCoffeeStore


def make_service(tmp_path: Path):
    return service_from_path(tmp_path / "coffee.sqlite3")


def test_repeated_failure_triggers_checkpoint(tmp_path):
    service = make_service(tmp_path)

    for _ in range(3):
        result = service.report_event(
            agent_id="codex",
            run_id="run-1",
            event_type="tool_error",
            success=False,
            error_kind="test_failure",
            tool_name="pytest",
            command="pytest -q",
            message="same assertion failed",
        )

    recovery = result["recovery"]
    state = result["state"]

    assert state["status"] == "stuck"
    assert state["repeated_failure_count"] == 3
    assert recovery["severity"] == "high"
    assert recovery["action"] == "create_checkpoint"
    assert "checkpoint" in recovery["suggested_next_step"].lower()


def test_context_pressure_triggers_compaction(tmp_path):
    service = make_service(tmp_path)

    result = service.report_event(
        agent_id="codex",
        run_id="run-context",
        event_type="context_pressure",
        success=True,
        tokens=90_000,
        message="context window is getting large",
    )

    recovery = result["recovery"]

    assert recovery["severity"] == "high"
    assert recovery["action"] == "compact_context"


def test_take_break_resets_active_loop_analysis(tmp_path):
    service = make_service(tmp_path)

    for _ in range(3):
        service.report_event(
            agent_id="codex",
            run_id="run-2",
            event_type="tool_error",
            success=False,
            error_kind="command_failed",
            command="npm test",
            message="same command failed",
        )

    before = service.recommend_recovery(agent_id="codex", run_id="run-2")
    assert before["recovery"]["action"] == "create_checkpoint"

    break_plan = service.take_break(agent_id="codex", run_id="run-2", reason="checkpoint before retry")

    assert break_plan.recovery.action == "create_checkpoint"
    assert break_plan.state_after_break.status == "steady"
    assert break_plan.state_after_break.repeated_failure_count == 0


def test_store_persists_events(tmp_path):
    db_path = tmp_path / "coffee.sqlite3"
    service = service_from_path(db_path)
    service.report_event(agent_id="codex", run_id="run-3", event_type="progress", message="started")

    reopened = SQLiteCoffeeStore(db_path)
    events = reopened.get_events("codex", "run-3")

    assert len(events) == 1
    assert events[0].message == "started"


def test_mcp_server_module_imports_without_sdk():
    from agent_need_coffee import mcp_server

    assert hasattr(mcp_server, "main")


def test_mcp_server_registers_when_sdk_is_available():
    pytest.importorskip("mcp")

    from agent_need_coffee import mcp_server

    assert mcp_server.mcp is not None


def test_repository_skill_metadata_exists():
    root = Path(__file__).resolve().parents[1]
    skill = root / "skills" / "agent-need-coffee" / "SKILL.md"
    metadata = root / "skills" / "agent-need-coffee" / "agents" / "openai.yaml"

    assert skill.exists()
    assert metadata.exists()

    skill_text = skill.read_text(encoding="utf-8")
    metadata_text = metadata.read_text(encoding="utf-8")

    assert "name: agent-need-coffee" in skill_text
    assert "coffee_report_event" in skill_text
    assert "$agent-need-coffee" in metadata_text
