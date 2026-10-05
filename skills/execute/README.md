# Execute layer

Skills that take an issue from "ready to ship" to "merged on main." The Main thread orchestrates and reviews on the judgment model; execution subagents do the typing; Utility agents ([`agents/`](../../agents/)) on the cheapest capable model read CI logs, run test gates, fetch issues, assemble Review packets, and commit, so those dumps never enter Main-thread context. Role→model assignments are pinned in [`MODELS.md`](../../MODELS.md) — change them there first.

| Skill | Purpose |
|---|---|
| [`ship-issue`](./ship-issue/SKILL.md) | Drive a single Gitea issue end-to-end via a parallel-agent pipeline: Implementer in an isolated worktree → CI gate → Reviewer → CI gate → merge. Implementer brief reads `CONTEXT.md` and relevant ADRs; Reviewer treats vocabulary drift as a Blocker, not a nit. |
| [`milestone-builder`](./milestone-builder/SKILL.md) | Fan the `ship-issue` flow across an entire milestone in topological dependency order. Spawns Implementers in parallel per tier; merges into a milestone branch; opens a single milestone PR to main. |
| [`review`](./review/SKILL.md) | The Reviewer's procedure, invoked from the `ship-issue` / `milestone-builder` Stage 3 brief or directly with `/review <PR>`. A `review-prep` Utility agent assembles a Review packet (diff on disk, changed files, identifiers vs. `CONTEXT.md`, ADR hits, tests, hygiene, screenshots); the Reviewer reads it once, runs the Visual diff gate, and returns a fixed-shape report ending in a `verdict:` line. |
| [`milestone-e2e-test`](./milestone-e2e-test/SKILL.md) | Browser-based end-to-end validation of a milestone branch using Chrome MCP. Routes non-trivial bugs through `/diagnose`. |
| [`tdd`](./tdd/SKILL.md) | Test-driven development with a strict red-green-refactor loop in vertical slices. Invoked from implementer briefs when an issue lists testable behaviors. |
| [`diagnose`](./diagnose/SKILL.md) | Disciplined diagnosis loop for hard bugs. Build a deterministic feedback loop **first**, then hypothesize, instrument, fix, regression-test. |

See [`WORKFLOW.md`](../../WORKFLOW.md) for the per-issue and milestone flows in full.
