# Utility agents

Subagent definitions the plugin ships alongside its skills. Each is a **Utility agent** (see `CONTEXT.md`): a mechanical, well-bounded chore whose *output* is bulky but whose *judgment* is trivial, pinned to the cheapest capable model so the Main thread doesn't spend orchestrator-tier context on diffs, logs, and issue bodies. The model each one runs on is set in its frontmatter and tracked in [`MODELS.md`](../MODELS.md) — change it there first.

| Agent | Delegate to it for | Never for |
|---|---|---|
| [`commit`](./commit.md) | Staging named files and writing one conventional commit in the repo's existing style | Amending, rebasing, conflict resolution, pushing (unless briefed) |
| [`ci-check`](./ci-check.md) | Checking a PR's CI run and turning failed job logs into a classified digest | Fixing anything, re-running jobs |
| [`test-run`](./test-run.md) | Running local test / lint / format gates and reporting only failures with `path:line` | Editing files, installing dependencies |
| [`tracker-read`](./tracker-read.md) | Fetching issues, comments, milestones, PRs from Gitea as a digest that keeps IDs, dependency lines, ACs, and Comp References verbatim | Writing to the tracker |
| [`review-prep`](./review-prep.md) | Assembling the Review packet for a Reviewer: diff written to a scratch dir, changed-file table, new identifiers vs. `CONTEXT.md`, ADR hits, tests added, migration presence, PR hygiene, optional headless screenshots | Judging the code, posting reviews, editing anything |

## How skills use them

Skills refer to these by role and name — "delegate log reading to the `ci-check` Utility agent" — and spawn them with the `Agent` tool. Plugin agents are namespaced by plugin name, so the `subagent_type` is `ai-tools:commit`, `ai-tools:ci-check`, `ai-tools:test-run`, `ai-tools:tracker-read`, `ai-tools:review-prep` (the Agent tool's available-types list shows the exact string). The brief is the contract: give the agent the repo, the scope, and the word budget, and take the report as the only thing that enters Main-thread context.

Each file is a standard Claude Code agent definition: YAML frontmatter (`name`, `description`, `model`, `tools`) followed by the system prompt. The `description` is what the Main thread sees when choosing an agent type, so it states what to delegate and what not to.

## Escalation ladder

A Utility agent on the cheapest tier will sometimes miss a hard search or fail to parse an unfamiliar log. The fix is a retry on a stronger model for *that one brief*, not a permanently higher default. The ladder is a contract between the agent's report and the caller:

1. **Agent side.** Every search-type Utility agent (`ci-check`, `test-run`, `tracker-read`, `review-prep`) and the `Explore` override ends its report with a `confidence: found | partial | not-found` line, with the specific meaning of each value stated in the agent file. `commit` reports an `outcome:` line instead, because there is no stronger-model retry for a refused commit.
2. **Caller side.** On `found`, use the result. On `partial` or `not-found`, re-spawn the **same brief** once with `model:` set to the Escalation tier from [`MODELS.md`](../MODELS.md), quoting the first report's "what I checked / what is still unknown" so the retry doesn't repeat it. If the retry also comes back `partial` or `not-found`, the Main thread does the work itself — a third spawn on an Implementer- or Main-thread-tier model costs more than just reading the files.
3. **Never pre-escalate.** Don't start on the Escalation tier "because this one looks hard"; the whole point is that the cheap attempt is usually enough and the retry is cheap when it isn't.

The skills that delegate (`ship-issue`, `milestone-builder`, `review`) state this rule inline where they spawn a Utility agent. For non-skill sessions the same rule lives in the user-level `~/.claude/CLAUDE.md`, next to the Explore override.

## Local override of the built-in Explore agent

The same mechanism overrides Claude Code's built-in agents. As of Claude Code 2.1.x the built-in `Explore` agent runs with `model: inherit`, so every codebase sweep is billed at or near the orchestrator tier. Dropping an `Explore.md` whose frontmatter `model:` is the Utility-agent tier from [`MODELS.md`](../MODELS.md) into `~/.claude/agents/` replaces it for every project on that machine — user-level agents take precedence over built-in and plugin agents of the same name. The plugin deliberately does not ship that override; it's a per-machine cost preference, not a workflow contract.
