---
name: agent-need-coffee
description: Use when an AI agent is repeating failures, rerunning the same command, accumulating retries, hitting rate limits, facing context pressure, losing progress in a long task, or needing a checkpoint before continuing; instructs Codex to call the AgentNeedCoffee MCP tools and follow the returned recovery action.
---

# AgentNeedCoffee

Use this skill to keep an agent from continuing an unproductive loop. The MCP
server is the source of truth for state and recommendations.

## Required MCP Tools

Prefer these tools when available:

- `coffee_report_event`
- `coffee_get_state`
- `coffee_recommend_recovery`
- `coffee_take_break`
- `coffee_clear_run`

If the MCP server is not available, use the same workflow manually: write a
checkpoint, identify the repeated failure signature, and choose one smaller next
step.

## When To Report Events

Call `coffee_report_event` after any meaningful event that affects control flow:

- command, test, model, or tool failure
- repeated retry
- API rate limit or timeout
- context pressure or compaction need
- long-running task with no clear progress
- successful progress after a previous failure

Use stable `agent_id` and `run_id` for the task. Reuse the same `signature` for
the same failure pattern so loop detection works.

## Event Shapes

For a failing command:

```json
{
  "event_type": "tool_error",
  "success": false,
  "tool_name": "shell",
  "command": "pytest -q",
  "error_kind": "test_failure",
  "message": "same assertion failed",
  "signature": "pytest-same-assertion"
}
```

For context pressure:

```json
{
  "event_type": "context_pressure",
  "success": true,
  "tokens": 90000,
  "message": "context is large; compaction may be needed"
}
```

For successful progress:

```json
{
  "event_type": "progress",
  "success": true,
  "message": "targeted test passed after narrowing the fix"
}
```

## How To Use Recommendations

After `coffee_report_event` or `coffee_recommend_recovery`, treat `recovery` as
a control-flow instruction:

- `continue`: proceed normally.
- `continue_with_smaller_step`: state one hypothesis and run one narrow check.
- `backoff`: pause retries, reduce request size/frequency, then retry once.
- `compact_context`: summarize current goal, evidence, changed files, and next action.
- `create_checkpoint`: stop broad execution and write a compact recovery checkpoint.
- `ask_human`: do not keep retrying; summarize the loop and ask for direction.

Do not repeat the same failing command unchanged after a `high` or `critical`
recommendation.

## Coffee Break Checkpoint

Call `coffee_take_break` when the recommendation says to checkpoint or when the
agent is about to pause and resume later. The break resets active loop analysis
for future events while keeping history in the timeline.

A good checkpoint contains:

- current goal
- last verified evidence
- failed attempts
- dominant failure signature
- one smallest next action

## Recovery Review Prompt

If the client exposes MCP prompts, use `coffee_recovery_review` for a compact
run review before continuing from a stuck state.
