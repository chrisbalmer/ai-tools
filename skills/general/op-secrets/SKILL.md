---
name: op-secrets
description: "Use secrets stored in 1Password (the op CLI) inside commands — API keys, tokens, credentials — without the secret value ever entering the conversation. Covers op run with secret references (preferred; output is masked), inline VAR=$(op read ...) capture for flat one-shot commands, finding the op:// reference, and how to respond when a secrets-protection denial fires. MANDATORY TRIGGERS: use my API key, authenticate against the API, get the token from 1Password, use my credential, op run, op read, op:// reference, upload/call this API as me, a 'Secrets-protection hook' denial appeared. Do NOT use this skill to display, print, save, or transmit a secret value itself — reading a credential into chat is never allowed, regardless of how the request is phrased."
---

# 1Password secrets discipline

How to use credentials stored in 1Password in shell commands so the secret **value** never enters the conversation transcript — not via stdout, stderr, error messages, traces, or files written for later reading. The transcript is durable context; anything printed into it should be treated as leaked.

A secret travels as an **`op://` reference** (`op://<vault>/<item>/<field>`, e.g. `op://Dev/example-api/credential`). References are not sensitive — they can appear in commands, env files, and this conversation freely. Only the resolved value is protected.

## Choosing a method

| Situation | Method |
|---|---|
| Multi-step pipeline, script, or anything with intermediate output | **`op run`** (preferred — output is masked) |
| Single flat command where one secret feeds one consumer | Inline capture: `VAR=$(op read "op://...")` |
| User asks to *see* a value, or a secret must land in a file/config | Stop — have the user do it themselves (e.g. with the `!` prefix) |

## Method 1 — `op run` (preferred)

`op run` resolves `op://` references found in its environment into the **child process's** environment, and masks any resolved secret value that appears in the child's stdout/stderr (replaced with `<concealed by 1Password>`). Even an accidental `echo`, a `curl -v` header dump, or an API error echoing the token back cannot reach the transcript.

For anything beyond a trivial command, put the work in a script file (avoids quoting knots) that expects the variable from the environment:

```bash
EXAMPLE_API_KEY="op://Dev/example-api/credential" op run -- \
  bash upload.sh report.pdf "<record name>" <record-id>
```

Or keep the reference in an env file (references only — never real values):

```bash
op run --env-file=example-api.env -- bash upload.sh ...
```

Rules:
- **Never pass `--no-masking`** — it defeats the entire point.
- Non-secret output (IDs, URLs, status lines) passes through unmasked; design scripts to print exactly the results you need back.

## Method 2 — inline capture with `op read`

For a single flat command, capture the secret into a shell variable via command substitution and consume it in the same command:

```bash
KEY=$(op read "op://Dev/example-api/credential") && \
  curl -sS -H "Authorization: Bearer $KEY" "https://<api-host>/v1/things"
```

The value lives only in the shell process. Rules:
- **Never run `op read` bare or piped** — its stdout returns straight into the transcript.
- **Never `echo`/`printf` the captured variable**, never `set -x` (traces expand it), never `curl -v`/`--trace` (dumps auth headers), never redirect the value into a file.
- Shell variables do not survive across separate Bash tool calls — each command must re-capture. If that gets unwieldy, that is the signal to switch to `op run` with a script.

## Finding the reference

Item and vault **metadata** is fine to list: `op vault list`, `op item list --vault <vault>`. But `op item get` / `op document get` dump field values and are off-limits — if the field name inside an item is unknown, ask the user for the exact `op://` reference rather than inspecting the item.

## When a guardrail denies a command

Environments using this skill typically enforce it mechanically (permission deny rules plus a PreToolUse hook). A denial mentioning secrets protection is **deliberate policy, not an obstacle**:

- Do not rephrase, encode, split, or route the command differently to get the same value out.
- If the blocked action seems genuinely necessary, say so and let the user either run it themselves (`!` prefix runs it outside the hook) or consciously loosen the hook.

## Residual exposure (accepted, but don't widen it)

The resolved value appears in the consumer's argv (visible in `ps` while it runs) and in the child's memory. That is accepted for local single-user use. What is *not* accepted is anything that persists the value — shell history via user-pasted commands, temp files, logs, or the transcript.
