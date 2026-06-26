from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path
from typing import Any

from .models import AgentEvent, RecoveryAction, utc_now


def default_db_path() -> Path:
    configured = os.environ.get("AGENT_NEED_COFFEE_DB")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".agent_need_coffee" / "coffee.sqlite3"


class SQLiteCoffeeStore:
    """Small SQLite store for local stdio MCP usage."""

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else default_db_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    tokens INTEGER NOT NULL,
                    retries INTEGER NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    error_kind TEXT NOT NULL,
                    tool_name TEXT NOT NULL,
                    command TEXT NOT NULL,
                    message TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_agent_run
                    ON events(agent_id, run_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_events_run
                    ON events(run_id, created_at);

                CREATE TABLE IF NOT EXISTS breaks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    action TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_breaks_agent_run
                    ON breaks(agent_id, run_id, created_at);
                """
            )

    def record_event(self, event: AgentEvent) -> int:
        signature = event.loop_signature()
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO events (
                    agent_id, run_id, event_type, success, tokens, retries,
                    latency_ms, error_kind, tool_name, command, message,
                    signature, created_at, payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.agent_id,
                    event.run_id,
                    event.event_type,
                    int(event.success),
                    event.tokens,
                    event.retries,
                    event.latency_ms,
                    event.error_kind,
                    event.tool_name,
                    event.command,
                    event.message,
                    signature,
                    event.created_at,
                    json.dumps(event.payload, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def record_break(self, agent_id: str, run_id: str, recovery: RecoveryAction) -> int:
        payload = recovery.model_dump(mode="json")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO breaks (
                    agent_id, run_id, severity, action, reason, created_at, payload
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    run_id,
                    recovery.severity,
                    recovery.action,
                    recovery.reason,
                    utc_now(),
                    json.dumps(payload, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def get_events(
        self,
        agent_id: str,
        run_id: str,
        *,
        since: str | None = None,
        limit: int = 200,
    ) -> list[AgentEvent]:
        sql = """
            SELECT * FROM events
            WHERE agent_id = ? AND run_id = ?
        """
        params: list[Any] = [agent_id, run_id]
        if since:
            sql += " AND created_at > ?"
            params.append(since)
        sql += " ORDER BY created_at ASC, id ASC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_run_events(self, run_id: str, *, limit: int = 200) -> list[AgentEvent]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM events
                WHERE run_id = ?
                ORDER BY created_at ASC, id ASC
                LIMIT ?
                """,
                (run_id, limit),
            ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def get_last_break(self, agent_id: str, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT * FROM breaks
                WHERE agent_id = ? AND run_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (agent_id, run_id),
            ).fetchone()

        if row is None:
            return None

        return {
            "id": row["id"],
            "agent_id": row["agent_id"],
            "run_id": row["run_id"],
            "severity": row["severity"],
            "action": row["action"],
            "reason": row["reason"],
            "created_at": row["created_at"],
            "payload": json.loads(row["payload"] or "{}"),
        }

    def clear_run(self, agent_id: str, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute("DELETE FROM events WHERE agent_id = ? AND run_id = ?", (agent_id, run_id))
            conn.execute("DELETE FROM breaks WHERE agent_id = ? AND run_id = ?", (agent_id, run_id))

    def _row_to_event(self, row: sqlite3.Row) -> AgentEvent:
        return AgentEvent(
            agent_id=row["agent_id"],
            run_id=row["run_id"],
            event_type=row["event_type"],
            success=bool(row["success"]),
            tokens=row["tokens"],
            retries=row["retries"],
            latency_ms=row["latency_ms"],
            error_kind=row["error_kind"],
            tool_name=row["tool_name"],
            command=row["command"],
            message=row["message"],
            signature=row["signature"],
            created_at=row["created_at"],
            payload=json.loads(row["payload"] or "{}"),
        )
