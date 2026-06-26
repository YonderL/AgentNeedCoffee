# AgentNeedCoffee

AgentNeedCoffee is a local Model Context Protocol (MCP) server that helps AI
agents recover from bad control flow: repeated failed commands, blind retries,
context pressure, rate limits, and long-running work without progress.

The coffee metaphor stays, but the product is now a recovery layer. A "coffee
break" records a checkpoint and changes how the next recommendation is computed.

## Why It Exists

Most agent failures are not caused by a lack of model intelligence. They happen
when the agent keeps doing the same unproductive thing:

- rerunning the same failing command
- retrying a flaky tool without changing any variable
- continuing after the context has become too large
- editing more code before isolating the failing assumption
- failing to ask for human input when autonomous progress is unlikely

AgentNeedCoffee gives the agent a small external memory and policy engine. The
agent reports what is happening, then the MCP server returns a concrete recovery
action such as `create_checkpoint`, `compact_context`, `backoff`, or `ask_human`.

## Architecture

AgentNeedCoffee is local-first. It does not require a cloud server, domain, open
port, account system, or hosted database.

```text
AI agent / MCP client
        |
        | stdio MCP
        v
agent-need-coffee-mcp
        |
        | records events, evaluates policy
        v
SQLite state store
```

The MCP client starts `agent-need-coffee-mcp` as a local process and communicates
with it over standard input/output. The server persists state in SQLite so it can
remember a run across tool calls and process restarts.

Default state path:

```text
~/.agent_need_coffee/coffee.sqlite3
```

Override it when needed:

```bash
export AGENT_NEED_COFFEE_DB=/path/to/coffee.sqlite3
```

## Runtime Workflow

1. The MCP client starts `agent-need-coffee-mcp`.
2. The agent calls `coffee_report_event` after meaningful runtime events.
3. The server stores the event in SQLite.
4. The policy engine calculates the current agent state.
5. The server returns a structured recovery recommendation.
6. The agent changes its next action based on that recommendation.
7. If the agent calls `coffee_take_break`, the server records a checkpoint and
   resets active loop analysis for future events.

The server does not magically control the model. It improves the agent by giving
it an external control-flow signal that is harder to ignore than internal
reasoning alone.

## Install

Requires Python 3.10 or newer. Python 3.9 cannot install the current MCP SDK.

```bash
pip install agent-need-coffee
```

For local development from this repository:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## MCP Client Configuration

Use this command in any MCP-capable client:

```bash
agent-need-coffee-mcp
```

Generic MCP configuration:

```json
{
  "mcpServers": {
    "agent-need-coffee": {
      "command": "agent-need-coffee-mcp"
    }
  }
}
```

For development from a checkout:

```json
{
  "mcpServers": {
    "agent-need-coffee": {
      "command": "python",
      "args": ["-m", "agent_need_coffee.mcp_server"],
      "env": {
        "PYTHONPATH": "/absolute/path/to/AgentNeedCoffee/src"
      }
    }
  }
}
```

## When The Agent Should Call It

| Situation | Tool call | Expected effect |
| --- | --- | --- |
| A command, tool, or test fails | `coffee_report_event` | Records evidence and updates loop detection |
| The same failure repeats | `coffee_recommend_recovery` | Returns `create_checkpoint` or `ask_human` |
| Context is too large | `coffee_report_event` with `context_pressure` | Returns `compact_context` |
| Rate limits or retries accumulate | `coffee_report_event` with `rate_limit` or retries | Returns `backoff` |
| The agent needs a reset point | `coffee_take_break` | Records a break and resets active loop analysis |
| A run should start fresh | `coffee_clear_run` | Deletes local state for that run |

## Tool Reference

### `coffee_report_event`

Records a runtime event and immediately returns updated state plus a recovery
recommendation.

Useful event types:

- `progress`
- `model_call`
- `tool_call`
- `tool_error`
- `test_failure`
- `retry`
- `rate_limit`
- `context_pressure`
- `checkpoint`

Example input:

```json
{
  "agent_id": "codex",
  "run_id": "fix-tests-42",
  "event_type": "tool_error",
  "success": false,
  "error_kind": "test_failure",
  "tool_name": "pytest",
  "command": "pytest -q",
  "message": "same assertion failed",
  "signature": "pytest-same-assertion"
}
```

Example output after repeated failures:

```json
{
  "state": {
    "status": "stuck",
    "failure_events": 3,
    "repeated_failure_count": 3,
    "dominant_failure_signature": "pytest-same-assertion"
  },
  "recovery": {
    "severity": "high",
    "action": "create_checkpoint",
    "reason": "The agent appears stuck in a failure loop.",
    "suggested_next_step": "Create a compact checkpoint, then choose one smaller verification step before continuing."
  }
}
```

### `coffee_get_state`

Returns the current health state for an agent run since the last coffee break.

### `coffee_recommend_recovery`

Returns a structured recommendation without recording a new event.

Possible actions:

- `continue`
- `continue_with_smaller_step`
- `backoff`
- `compact_context`
- `create_checkpoint`
- `ask_human`
- `stop_loop`

### `coffee_take_break`

Records a coffee checkpoint and resets active loop analysis for future events.
Historical events remain available in the run timeline.

### `coffee_clear_run`

Clears local state for one agent/run pair. Use only when intentionally starting
over.

## Resources And Prompt

Resources:

```text
coffee://agents/{agent_id}/state
coffee://runs/{run_id}/timeline
```

Prompt:

```text
coffee_recovery_review
```

The prompt asks the agent to write a compact checkpoint containing the current
goal, evidence, failed attempts, dominant failure signature, and exactly one next
action.

## Policy Summary

The policy engine computes three scores:

- `fatigue_score`: token volume, retry count, and run duration
- `friction_score`: failure volume, repeated failures, and rate limits
- `loop_score`: how strongly one failure signature is repeating

The server then maps those scores to recovery actions:

| Signal | Action |
| --- | --- |
| No concerning events | `continue` |
| Multiple unrelated failures | `continue_with_smaller_step` |
| Retries or rate limits | `backoff` |
| High token/context pressure | `compact_context` |
| Repeated failure loop | `create_checkpoint` |
| Persistent repeated loop | `ask_human` |

## Development

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
pytest -q
```

Run the MCP server directly:

```bash
AGENT_NEED_COFFEE_DB=/tmp/coffee.sqlite3 agent-need-coffee-mcp
```

The implementation uses the official Python MCP SDK with `FastMCP` and the
default stdio transport.
