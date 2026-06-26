<h1 align="center">AgentNeedCoffee</h1>

<p align="center">
  <strong>A local MCP recovery layer for AI agents that get stuck, retry blindly, or lose control of long-running work.</strong>
</p>

<p align="center">
  <a href="https://github.com/YonderL/AgentNeedCoffee"><img alt="MCP" src="https://img.shields.io/badge/MCP-local%20stdio-6f4e37?style=for-the-badge"></a>
  <a href="https://github.com/YonderL/AgentNeedCoffee"><img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776ab?style=for-the-badge"></a>
  <a href="https://github.com/YonderL/AgentNeedCoffee"><img alt="Storage" src="https://img.shields.io/badge/State-SQLite-003b57?style=for-the-badge"></a>
  <a href="https://github.com/YonderL/AgentNeedCoffee/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/badge/License-MIT-111827?style=for-the-badge"></a>
</p>

<p align="center">
  <code>coffee_report_event</code> . <code>coffee_recommend_recovery</code> . <code>coffee_take_break</code> . <code>coffee_recovery_review</code>
</p>

---

## The Idea

AI agents do not only fail because they lack reasoning ability. They often fail
because their control flow degrades:

- the same command is rerun without changing the hypothesis
- the same tool error is retried until the context fills up
- rate limits trigger a noisy retry loop
- a long task continues without a checkpoint
- the agent should ask for help, but keeps acting

AgentNeedCoffee gives the agent a local MCP server that records runtime events,
detects loops, and returns a concrete recovery action.

<table>
  <tr>
    <td><strong>Detect</strong></td>
    <td>Repeated failures, retries, rate limits, and context pressure.</td>
  </tr>
  <tr>
    <td><strong>Decide</strong></td>
    <td>Map run state to actions like <code>backoff</code>, <code>compact_context</code>, or <code>ask_human</code>.</td>
  </tr>
  <tr>
    <td><strong>Recover</strong></td>
    <td>Create checkpoints so the agent resumes from evidence, not habit.</td>
  </tr>
</table>

## MCP + Skill

AgentNeedCoffee is now two pieces:

| Piece | Role | Lives in |
| --- | --- | --- |
| MCP server | Stores state and returns recovery actions | `src/agent_need_coffee/mcp_server.py` |
| Agent skill | Teaches the agent when and how to call the MCP tools | `skills/agent-need-coffee/` |

The MCP server is the runtime. The skill is the operating procedure.

## Architecture

```text
AI agent / MCP client
        |
        | stdio MCP
        v
agent-need-coffee-mcp
        |
        | record event -> evaluate policy -> return recovery action
        v
SQLite state store
```

AgentNeedCoffee is local-first. It does not need a hosted API, account system,
open port, or cloud database.

Default state path:

```text
~/.agent_need_coffee/coffee.sqlite3
```

Override it:

```bash
export AGENT_NEED_COFFEE_DB=/path/to/coffee.sqlite3
```

## Runtime Flow

```text
1. Agent runs work
2. Something meaningful happens
3. Agent calls coffee_report_event
4. Server persists the event
5. PolicyEngine calculates run health
6. Server returns a recovery action
7. Agent changes its next move
```

If the agent calls `coffee_take_break`, the server records a checkpoint and
resets active loop analysis for future events. Historical events remain in the
timeline.

## Install

Requires Python 3.10 or newer. Python 3.9 cannot install the current MCP SDK.

```bash
pip install agent-need-coffee
```

For local development:

```bash
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

## MCP Client Configuration

Use the installed command:

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

Development checkout configuration:

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

## Install The Skill

The repository includes a Codex/Agent skill that tells the agent when to call
AgentNeedCoffee.

```bash
cp -R skills/agent-need-coffee "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Once installed, the skill triggers when the agent repeats failures, accumulates
retries, hits rate limits, faces context pressure, or needs a checkpoint. It then
instructs the agent to call the MCP tools and follow the returned action.

## Tool Reference

<table>
  <tr>
    <th>Tool</th>
    <th>Use it when</th>
    <th>What it returns or changes</th>
  </tr>
  <tr>
    <td><code>coffee_report_event</code></td>
    <td>A command, test, model call, or tool call succeeds or fails.</td>
    <td>Stores the event and returns updated state plus recovery advice.</td>
  </tr>
  <tr>
    <td><code>coffee_get_state</code></td>
    <td>The agent needs current run health.</td>
    <td>Returns scores, counters, status, and dominant failure signature.</td>
  </tr>
  <tr>
    <td><code>coffee_recommend_recovery</code></td>
    <td>No new event happened, but the agent needs a decision.</td>
    <td>Returns a structured recovery action.</td>
  </tr>
  <tr>
    <td><code>coffee_take_break</code></td>
    <td>The agent needs to checkpoint before continuing.</td>
    <td>Records a break and resets active loop analysis.</td>
  </tr>
  <tr>
    <td><code>coffee_clear_run</code></td>
    <td>The run is intentionally starting over.</td>
    <td>Deletes local state for one agent/run pair.</td>
  </tr>
</table>

## Example Event

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

Example recovery after repeated failures:

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

## Recovery Actions

| Action | Meaning |
| --- | --- |
| `continue` | The run is steady. Proceed normally. |
| `continue_with_smaller_step` | Narrow the next action to one hypothesis. |
| `backoff` | Pause retries and reduce frequency or request size. |
| `compact_context` | Summarize the run before continuing. |
| `create_checkpoint` | Stop broad execution and write a recovery checkpoint. |
| `ask_human` | Do not keep retrying; ask for direction. |

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

## Policy Model

The policy engine computes:

- `fatigue_score`: token volume, retry count, and run duration
- `friction_score`: failure volume, repeated failures, and rate limits
- `loop_score`: how strongly one failure signature is repeating

It then maps those signals to recovery actions:

```text
steady -> continue
minor failures -> continue_with_smaller_step
retries/rate limits -> backoff
context pressure -> compact_context
repeated failure -> create_checkpoint
persistent loop -> ask_human
```

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
