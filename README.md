# AgentNeedCoffee

AgentNeedCoffee is a local MCP server that helps AI agents notice when they are
stuck, checkpoint their work, and recover instead of repeating the same failing
step.

The "coffee break" is not a cosmetic pause. It records a recovery checkpoint and
changes the next recommendation for the run.

## What It Does

AgentNeedCoffee gives MCP-capable agents tools to:

- report model, tool, command, test, retry, rate-limit, and context-pressure events
- persist run state locally in SQLite
- detect repeated failure loops
- recommend concrete recovery actions
- create a break/checkpoint that resets active loop analysis
- expose state and timelines as MCP resources

The server is local-first. It runs over stdio, so you do not need a cloud server,
domain, open port, or hosted API.

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

## Run As A Local stdio MCP Server

```bash
agent-need-coffee-mcp
```

MCP clients normally start this command for you.

Example client configuration:

```json
{
  "mcpServers": {
    "agent-need-coffee": {
      "command": "agent-need-coffee-mcp"
    }
  }
}
```

The server stores data at:

```text
~/.agent_need_coffee/coffee.sqlite3
```

Override it with:

```bash
export AGENT_NEED_COFFEE_DB=/path/to/coffee.sqlite3
```

## MCP Tools

### `coffee_report_event`

Record an agent runtime event and immediately get an updated recovery
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

Example:

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

After repeated failures, the tool returns:

```json
{
  "recovery": {
    "severity": "high",
    "action": "create_checkpoint",
    "reason": "The agent appears stuck in a failure loop.",
    "suggested_next_step": "Create a compact checkpoint, then choose one smaller verification step before continuing."
  }
}
```

### `coffee_get_state`

Return the current health state for an agent run since the last coffee break.

### `coffee_recommend_recovery`

Return a structured recovery action without recording a new event.

Actions include:

- `continue`
- `continue_with_smaller_step`
- `backoff`
- `compact_context`
- `create_checkpoint`
- `ask_human`
- `stop_loop`

### `coffee_take_break`

Create a coffee checkpoint, record a break, and reset active loop analysis for
future events. Historical events remain in the timeline.

### `coffee_clear_run`

Clear local state for one agent run when intentionally starting over.

## MCP Resources

```text
coffee://agents/{agent_id}/state
coffee://runs/{run_id}/timeline
```

## MCP Prompt

```text
coffee_recovery_review
```

This prompt generates a compact recovery review for a stuck run. It asks the
agent to summarize the goal, evidence, failed attempts, dominant failure
signature, and exactly one next action.

## Why This Helps Agents

Many agent failures are not reasoning failures; they are control-flow failures.
The agent repeats the same command, retries the same API, keeps editing without
a narrowing hypothesis, or continues after context has become too large.

AgentNeedCoffee gives the agent a small external memory and policy layer so it
can:

- detect that a loop is happening
- stop blind retries
- compact context at the right time
- checkpoint before continuing
- ask for human input when autonomous progress is unlikely

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
