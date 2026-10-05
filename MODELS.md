# MODELS.md — role→model mapping for the agent flows

The execute-layer skills (`ship-issue`, `milestone-builder`, `review`) spawn subagents with explicit `model:` overrides on the `Agent` tool, and the Utility agents in `agents/` pin their model in frontmatter. This file is the **single source of truth** for which model plays which role, and the procedure for changing the assignment. Change the table here first, then propagate with the checklist below.

Why this file exists: model assignments are expected to churn — pricing changes, models become available or unavailable, or a role gets tuned to a different tier. The repo is written so that a swap touches a short list of canonical locations instead of every skill. Everywhere else, prose refers to the **role names** pinned in `CONTEXT.md` (Main thread, Implementer, Reviewer, Fix agent, Utility agent, and the Escalation tier), never to model names.

## Current mapping (since 2026-06-11)

| Role (`CONTEXT.md` term) | Model | How it's set |
|---|---|---|
| Main thread (orchestrator / arbiter) | `fable` | The session model — the user sets it via `/model`; skills can only document the expectation |
| Implementer | `opus` | `model:` field in the Agent-call examples (locations below) |
| Reviewer | `fable` | same |
| Fix agent | `opus` | same |
| Utility agent | `haiku` | `model:` in the frontmatter of each `agents/*.md` file (commit, ci-check, test-run, tracker-read, review-prep) |
| Escalation tier (one retry of a Utility-agent brief) | `sonnet` | Passed as `model:` on the retry spawn; no role defaults to it |

The contract in the current mapping: **fable thinks, opus types, haiku fetches.** Utility agents exist to keep bulky-but-trivial output (diffs, CI logs, test-runner output, issue bodies, PR diffs for review) out of Main-thread context; they make no judgment calls and write no application code, so the cheapest capable model is the right tier.

Guiding principles when tuning:

- **The Reviewer must never run on a weaker model than the Implementer.** Weak reviewers pattern-match toward "approve" and miss subtle bugs, which silently removes the quality gate from the whole flow.
- The Main thread and Reviewer want the strongest long-context *judgment* model available; the Implementer and Fix agent want the strongest *execution* model you can afford, briefed concretely.
- **Escalation is per-brief, not per-role.** A Utility agent (or the Explore override) that reports `confidence: partial` / `not-found` gets one retry of the same brief on the Escalation tier; after that the Main thread does the work itself. See `agents/README.md` → Escalation ladder.
- **Utility agents never move up-tier to "be safe."** If a chore turns out to need judgment (a commit message that must explain a design decision, a log that needs interpretation against the spec), that work belongs to the Main thread or a Fix agent — split the task, don't upgrade the utility model.
- Whatever the mapping, the shape is "judgment model thinks, execution model types" — if both roles end up on the same model, the structural discipline (concrete briefs, no design latitude in implementer prompts, inline fixes under ~50 LOC) still applies; it's about context economy and clean handoffs, not just model rationing.

## Model-specific rationale (current mapping)

This is the only place that argues from model capabilities — prose in the skills argues only from the *shape* (judgment model thinks, execution model types). As of the current mapping: fable is strongest at long-context reasoning, spec interpretation, cross-ticket judgment, and the kind of careful reading that catches subtle bugs in review — so it takes Main thread and Reviewer. Opus is a strong, fast executor of well-specified tasks — so it takes Implementer and Fix agent, briefed concretely with no design latitude. Haiku is cheap and quick enough for fetch-and-summarize chores with a fixed report shape — so it takes the Utility agents, with sonnet as the one-retry Escalation tier when a haiku report comes back `partial` or `not-found`.

## Canonical locations — every file that names a model

If a `\b(sonnet|opus|haiku|fable)\b` grep hits a file not in this table, that's drift: rewrite the mention to a role name, or add the location here.

| File | What names a model there |
|---|---|
| `MODELS.md` (this file) | The mapping table, rationale, next mapping, history |
| `skills/execute/ship-issue/SKILL.md` | `model:` fields in the Stage 1 and Stage 3 Agent examples (with `// role — current mapping in MODELS.md` comments) |
| `skills/execute/milestone-builder/references/implementation-workflow.md` | `model:` fields in the Stage 1 and Stage 3 Agent examples (same comment convention) |
| `CONTEXT.md` | The _Avoid_ alias lists on the Implementer / Reviewer / Fix agent / Utility agent entries, and the "Flagged ambiguities" note about model-flavored names (these *ban* such names; they don't churn with the mapping) |
| `agents/*.md` (each Utility agent file) | Frontmatter `model:` — the only place the Utility-agent model is *set* |

(False-positive warning: "diffable" contains "fable" — use word boundaries in the grep, as above.)

## Procedure to change a model assignment

1. **Update the mapping table** at the top of this file, rewrite the "Model-specific rationale" section for the new mapping, and add a row to History with the date and reason.
2. **Verify the new value is a valid `Agent`-tool `model:` alias** (`sonnet`, `opus`, `haiku`, `fable` at time of writing). The skills use these stable aliases, never dated model IDs, so an alias keeps working across point releases.
3. **Edit the four `model:` fields** in the Agent examples: Stage 1 and Stage 3 in `skills/execute/ship-issue/SKILL.md`, and Stage 1 and Stage 3 in `skills/execute/milestone-builder/references/implementation-workflow.md`. (The Fix agent uses the same model as the Implementer per the Stage 4 note — no separate field.) If the Utility-agent tier changed, edit the frontmatter `model:` in each `agents/*.md` file; the Escalation tier has no field to edit.
4. **Sweep for drift**: `grep -rniE '\b(sonnet|opus|haiku|fable)\b' --include='*.md' .` — every hit should fall inside the canonical-locations table. Anything else is drift; fix it to a role name.
5. **If the *shape* of the split changed** (both roles on one model, a three-tier split), also revisit the "Model split" sections in the two execute skills — they argue the shape, not the models, so they only change when the shape does.
6. **Main thread is special**: skills cannot set the session model. If the orchestrator model changed, the user switches it with `/model`.
7. **Commit** with a message like `Swap Implementer to <model>, Reviewer to <model> (<reason>)`. Edits to skills are live for the next Claude Code session — nothing to build or restart.

## Next mapping — decided 2026-07-06, apply when fable is no longer available

| Role | Model |
|---|---|
| Main thread | `opus` |
| Implementer | `sonnet` |
| Reviewer | `opus` |
| Fix agent | `sonnet` |
| Utility agent | `haiku` (unchanged) |
| Escalation tier | `sonnet` (unchanged) |

Contract: "opus thinks, sonnet types." Rationale (decided, not provisional): opus plans everything out — briefs are concrete enough that sonnet is just following directions — and sonnet is preferred for execution because it's fast. Opus keeps Main thread and Reviewer (judgment work; Reviewer must never be weaker than the Implementer). One caution for that mapping: opus is a wordier model than fable — hold the line on the output caps in the skills (reviewer word caps, report-back caps, table row caps) rather than letting summaries and briefs inflate.

Applying it is the seven-step procedure above; steps 1–3 are the whole edit (this file plus four `model:` fields; the Utility-agent frontmatter doesn't change).

## History

| Date | Change | Reason |
|---|---|---|
| 2026-10-03 | Ported the 2026-07-06 role-name rule onto the newer content: Utility agent and Escalation tier rows added to the mapping and next-mapping tables; `agents/*.md` frontmatter added to the canonical locations; prose in `agents/README.md`, the `review` skill, `CONTEXT.md`, and the execute skills names roles and tiers only. | The Utility-agent and `review` work landed after the swap-surface reduction and had put model names back into prose. |
| 2026-09-11 | Added `agents/review-prep` (haiku) and the `review` skill; Reviewer now consumes a Review packet. | The Reviewer was spending judgment-model tokens fetching the diff via MCP, grepping ADRs, and re-reading spec files the brief already carried; the packet moves that to the cheapest tier. Reviewer model unchanged. |
| 2026-09-11 | Added Utility agent role on haiku (`agents/commit`, `ci-check`, `test-run`, `tracker-read`). | Usage limits were being consumed by orchestrator-tier tokens on mechanical chores; delegate bulky-output work to the cheapest model. |
| 2026-07-06 | Next mapping decided (opus judgment / sonnet execution on fable exit); swap surface reduced to this file + four `model:` example fields. | Planned model availability change; sonnet chosen for execution speed with opus pre-planning everything. |
| 2026-06-11 | Implementer / Fix agent: sonnet → opus. Main thread / Reviewer: opus → fable. | Fable became available; put the strongest judgment model on orchestration and review, opus on execution. |
| (before 2026-06-11) | Main thread / Reviewer: opus. Implementer / Fix agent: sonnet. | Original cost-tiered split. |
