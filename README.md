# ai-tools

A collection of **agent skills** for agent-driven development: self-contained behavior packages that a coding agent loads on demand to handle specialized workflows. The skills compose into a complete workflow (design → plan → execute → diagnose) with a shared **language layer** (`CONTEXT.md` + ADRs in the repo) that keeps parallel agent work from compounding into vocabulary drift and architectural mush.

The skills use the open `SKILL.md` format (YAML frontmatter plus a markdown body, with optional `references/` and `scripts/`), which Claude Code, Codex, opencode and Coder Agents all read. On top of that sits a **Claude Code layer**: the plugin and marketplace manifests in [`.claude-plugin/`](./.claude-plugin/), the Utility subagent definitions in [`agents/`](./agents/), and the role→model mapping in [`MODELS.md`](./MODELS.md). The language, plan and general skills are agent-agnostic. The execute layer (`ship-issue`, `milestone-builder`, `milestone-e2e-test`, `review`) assumes Claude Code's `Agent` and `Skill` tools, a Gitea-compatible MCP server (`mcp__gitea__*`) and, for `milestone-e2e-test`, Chrome MCP.

> [!tip] New to this repo?
> Read [`WORKFLOW.md`](./WORKFLOW.md) — the end-to-end manual for *using* the skill set.
> Read [`CONTEXT.md`](./CONTEXT.md) — the meta-glossary that pins the vocabulary the skills themselves use (Skill, Implementer, Reviewer, Main thread, Worktree, Milestone branch, Vault, Repo, etc.). Read it before editing any SKILL.md.

## Install

**Claude Code.** The repo is a plugin marketplace containing a single plugin (`ai-tools`):

```
/plugin marketplace add chrisbalmer/ai-tools
/plugin install ai-tools@ai-tools
```

Skills then appear under the `/ai-tools:` namespace (e.g. `/ai-tools:grill-with-docs`, `/ai-tools:ship-issue`), and the Utility agents as `ai-tools:<name>`. The plugin enumerates skills and agents explicitly in [`.claude-plugin/plugin.json`](./.claude-plugin/plugin.json) — adding a new skill requires updating that file as well.

**Other agents** (Codex, opencode, Coder Agents) will get the agent-agnostic skills through an installer, coming later; the execute layer needs Claude Code.

## What are skills?

A skill is a directory under `skills/` that teaches a coding agent how to handle a specific domain. When a user says something matching a skill's trigger phrases, the agent loads the skill and follows its instructions. There is nothing to build or deploy — editing a skill file makes it live immediately for the next session.

```
skills/<bucket>/<skill-name>/
  SKILL.md          # required — YAML frontmatter + body
  references/*.md   # optional — loaded on demand during execution
  scripts/          # optional — executable helpers (Python stdlib preferred)
```

Buckets organize skills by their role: [`language/`](./skills/language/), [`plan/`](./skills/plan/), [`execute/`](./skills/execute/), [`general/`](./skills/general/). Each bucket's `README.md` lists its members.

## The three layers

The skills break into three layers. Most large-project failure modes (entropy across milestones, vocabulary drift, accumulated bugs that point at architectural mush) come from missing the **language** layer entirely — using only **plan** + **execute** compounds drift because every agent works in a context-poor environment.

| Layer | Purpose | Skills |
|---|---|---|
| **Language** | Shared vocabulary and decisions that travel with the code | [`grill-with-docs`](./skills/language/grill-with-docs/), [`improve-codebase-architecture`](./skills/language/improve-codebase-architecture/) |
| **Plan** | Turn intent into structured, sliceable work | [`app-design`](./skills/plan/app-design/) (heavy, greenfield), [`to-prd`](./skills/plan/to-prd/) + [`to-issues`](./skills/plan/to-issues/) (lightweight, brownfield), [`triage`](./skills/plan/triage/) |
| **Execute** | Take an issue from "ready to ship" to "merged" | [`ship-issue`](./skills/execute/ship-issue/), [`milestone-builder`](./skills/execute/milestone-builder/), [`review`](./skills/execute/review/), [`tdd`](./skills/execute/tdd/), [`diagnose`](./skills/execute/diagnose/), [`milestone-e2e-test`](./skills/execute/milestone-e2e-test/) |

Plus general-purpose helpers: [`obsidian-note`](./skills/general/obsidian-note/), [`session-note`](./skills/general/session-note/), [`op-secrets`](./skills/general/op-secrets/), [`har`](./skills/general/har/).

## Skills

### Language layer

#### [`grill-with-docs`](./skills/language/grill-with-docs/)
Interview the user about a plan, design, or change — challenging it against the project's domain glossary (`CONTEXT.md`) and architectural decisions (`docs/adr/`), updating both inline as decisions crystallize. The foundation for the language layer: every other skill reads what this one produces.

#### [`improve-codebase-architecture`](./skills/language/improve-codebase-architecture/)
Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. Writes a markdown report to `docs/architecture-review-<date>.md`. Run between milestones to keep parallel-implementer fan-out from compounding into a ball of mud.

### Plan layer

#### [`app-design`](./skills/plan/app-design/)
Heavy 8-phase design funnel for greenfield apps and major brownfield expansions. Vision → acceptance criteria → wireframes → architecture → stories → dependency graph → design review → issues. Produces Obsidian notes at each phase. Use for greenfield; reach for the lightweight pair for everything else.

#### [`to-prd`](./skills/plan/to-prd/)
Lightweight brownfield path — synthesize the current conversation into a single PRD and publish it as a Gitea issue. No interview; assumes you've already grilled the idea (manually or via `/grill-with-docs`).

#### [`to-issues`](./skills/plan/to-issues/)
Break a PRD or plan into independently-grabbable issues using **vertical-slice (tracer-bullet)** decomposition — each slice cuts through every layer end-to-end, not horizontally per layer.

#### [`triage`](./skills/plan/triage/)
Move Gitea issues through a state machine of triage roles (`needs-triage` → `ready-for-agent` etc.) with category labels (`bug` / `enhancement`). The gate `/ship-issue` and `/milestone-builder` expect — both refuse to start if an issue is still `needs-triage`.

### Execute layer

#### [`ship-issue`](./skills/execute/ship-issue/)
Drive a single Gitea issue from "ready to implement" to "merged on main" via a parallel-agent pipeline: Implementer in an isolated worktree → CI gate → Reviewer → CI gate → merge (role→model mapping in [`MODELS.md`](./MODELS.md)). Implementer brief includes `CONTEXT.md` + relevant ADRs; Reviewer scrutinizes vocabulary drift as a Blocker, not a nit.

#### [`milestone-builder`](./skills/execute/milestone-builder/)
Fan the `ship-issue` flow across an entire milestone in topological dependency order. Spawns Implementers in parallel per tier; gates on CI + review; merges into a milestone branch; opens a single milestone PR to main for human review.

#### [`review`](./skills/execute/review/)
The Reviewer's procedure: spec-adherence review of a PR against its issue, `CONTEXT.md`, ADRs, and any referenced Comps. The `review-prep` Utility agent assembles a **Review packet** (diff on disk, changed-file table, new identifiers vs. the glossary, ADR hits, tests added, PR hygiene, optional headless screenshots) so the Reviewer reads the diff once and spends its context on judgment. Returns a fixed-shape report ending in a `verdict:` line that `/ship-issue` and `/milestone-builder` Stage 4 key on. Invoke directly with `/review <PR>`; the execute flows invoke it from their Stage 3 briefs.

#### [`milestone-e2e-test`](./skills/execute/milestone-e2e-test/)
Browser-based end-to-end validation of a milestone branch using Chrome MCP. Finds bugs, files issues, routes non-trivial bugs through `/diagnose`, retests until clean.

#### [`tdd`](./skills/execute/tdd/)
Test-driven development with a strict red-green-refactor loop in vertical slices — one test → one implementation → repeat. Never "write all tests then all code." Invoked from `/ship-issue` and `/milestone-builder` implementer briefs when an issue lists testable behaviors.

#### [`diagnose`](./skills/execute/diagnose/)
Disciplined diagnosis loop for hard bugs. Build a fast, deterministic, agent-runnable feedback loop **first**, then hypothesize, instrument, fix, regression-test. Routed to from `/milestone-e2e-test` and from `/triage` when bug reproduction is non-trivial.

### General-purpose

#### [`obsidian-note`](./skills/general/obsidian-note/)
Create well-formatted markdown files for Obsidian with consistent frontmatter, structure, and wikilink conventions.

#### [`session-note`](./skills/general/session-note/)
Capture an end-of-session summary of the current Claude Code conversation as a dense Obsidian note — what was decided, why, what was built, what's still pending. Opinionated about format and location; complements the structured auto-memory `memory/` directory by holding the *rationale and ruled-out paths* that don't decompose into atomic facts.

#### [`op-secrets`](./skills/general/op-secrets/)
Use 1Password-stored credentials (API keys, tokens) in commands without the secret value ever entering the conversation — `op run` with `op://` secret references (preferred; 1Password masks any secret appearing in output) or inline `VAR=$(op read ...)` capture for flat one-shot commands. Also codifies how to respond when a secrets-protection guardrail denies a command: it's policy, not an obstacle.

#### [`har`](./skills/general/har/)
Process browser HAR network captures safely and repeatably: sanitize secrets and PII with a stdlib script, verify the redaction, read the capture through targeted digests (`list` / `keys` / `diff` / `show` / `extract`) instead of dumping it into the conversation, isolate the write-only keys a web UI adds on a read-modify-write, extract JSON fixtures, and record the findings in the project's observed-API doc. The standard path when an inferred endpoint comes back 404/405 and the real call has to be captured from the vendor's own UI.

## Utility agents

Skills describe *what* to do; [`agents/`](./agents/) ships five small subagent definitions for the mechanical chores the skills keep running into, each pinned to the cheapest capable model (the Utility-agent tier in [`MODELS.md`](./MODELS.md)). The Main thread delegates to them so orchestrator-tier context isn't spent on diffs, CI logs, test-runner output, and issue bodies.

| Agent | Delegate to it for |
|---|---|
| `commit` | Stage named files and write one conventional commit in the repo's style; no push |
| `ci-check` | Check a PR's CI run and turn failed job logs into a classified digest with the minimal excerpt |
| `test-run` | Run local test / lint / format gates and report only failures with `path:line` |
| `tracker-read` | Fetch issues, comments, milestones from Gitea as a digest that keeps IDs, dependency lines, ACs, and Comp References verbatim |
| `review-prep` | Assemble the Review packet for a Reviewer: diff on disk, changed-file table, new identifiers vs. `CONTEXT.md`, ADR hits, tests added, PR hygiene, optional headless screenshots |

The same mechanism overrides Claude Code's built-in agents: an `Explore.md` whose `model:` is the Utility-agent tier from `MODELS.md`, placed in `~/.claude/agents/` replaces the built-in Explore (which otherwise inherits the session model) on that machine. See [`agents/README.md`](./agents/README.md).

## Workflows at a glance

Full walkthroughs (greenfield, brownfield, bug, triage, UI redesign) are in [`WORKFLOW.md`](./WORKFLOW.md). Quick reference:

| Situation | Skills (in order) |
|---|---|
| New app from scratch | `/app-design` (Phases 1–8) → `/milestone-builder` → `/milestone-e2e-test` |
| Small feature on existing app | `/grill-with-docs` → `/to-prd` → `/to-issues` → `/ship-issue` |
| Large feature on existing app | `/app-design` (brownfield mode) → `/milestone-builder` |
| UI redesign | `/grill-with-docs` → sketch → `/to-prd` → `/to-issues` → `/ship-issue` with screenshot gate |
| Bug fix | `/triage` → `/diagnose` → `/ship-issue` |
| Codebase getting messy | `/improve-codebase-architecture` |
| Between milestones | `/improve-codebase-architecture` (catch entropy before next milestone) |

## Vault vs. repo split

A load-bearing convention used by the design and execute skills:

- **Obsidian vault** holds *thinking-time* artifacts: vision, acceptance criteria, wireframes, stories, dependency graph, design review.
- **Project repo** holds *living* artifacts that travel with the code: `CONTEXT.md` (domain glossary), `docs/adr/` (architectural decisions), architecture review reports.

`CONTEXT.md` is born in the vault during `/app-design` Phase 1–2 as terms emerge, then **moves to the repo root** at Phase 4 when the repo is created. After that, the repo is canonical and every Implementer / Reviewer agent reads from there.

## The app-design validator

`skills/plan/app-design/scripts/validate.py` is the app-design validator (Python 3.11+, stdlib only; the only other executables are the `har` skill's stdlib helpers in `skills/general/har/scripts/`). Run it against a design project directory (an Obsidian vault folder, not this repo):

```sh
python skills/plan/app-design/scripts/validate.py all <project-path>
python skills/plan/app-design/scripts/validate.py traceability <project-path>
python skills/plan/app-design/scripts/validate.py ujt-coverage <project-path>                    # opt-in
python skills/plan/app-design/scripts/validate.py vocab <project-path> --repo <repo-path>        # opt-in
```

The `vocab` subcommand flags Phase 8 issue bodies that have zero overlap with the repo's `CONTEXT.md` — a strong signal of vocabulary drift before the implementer flow picks the issues up.

Exit code equals the number of failures; `0` is a pass. See [`skills/plan/app-design/scripts/README.md`](./skills/plan/app-design/scripts/README.md) for full documentation.

## Conventions

- **`CONTEXT.md` at repo root pins the vocabulary the skills themselves use.** Read it before editing any `SKILL.md`. The skills cross-reference each other; consistent terms are what keep composition from drifting.
- **IDs are permanent.** `[V-NNN]`, `[AC-NNN]`, `[S-NNN]`, `[D-NNN]`, `[SCR-NNN]` — never renumber or reuse them across reworks.
- **Skills are isolated.** Cross-skill dependencies go through documented wikilinks (e.g., `[[grill-with-docs]]` or `[[language/grill-with-docs/references/CONTEXT-FORMAT.md]]`) or by the orchestrator spawning a sub-agent — never by importing files across skill boundaries.
- **No build surface.** Don't add a package manager, lockfile, or CI config at the repo root.

## Related documents

- [`WORKFLOW.md`](./WORKFLOW.md) — end-to-end developer workflow manual
- [`CONTEXT.md`](./CONTEXT.md) — meta-glossary for the skill set
- [`CLAUDE.md`](./CLAUDE.md) — guidance for Claude Code sessions working in this repo
- [`THIRD_PARTY_LICENSES.md`](./THIRD_PARTY_LICENSES.md) — attribution and license text for skills adapted from upstream sources

## Credits

Seven of the skills in this repo (`grill-with-docs`, `improve-codebase-architecture`, `to-prd`, `to-issues`, `tdd`, `diagnose`, `triage`) are adapted from [mattpocock/skills](https://github.com/mattpocock/skills) — Matt Pocock's collection of engineering skills for Claude Code, licensed under MIT. The original work introduced the `CONTEXT.md` + `docs/adr/` convention, the deepening / shallow-modules vocabulary, the red-green-refactor TDD discipline, the feedback-loop-first diagnosis pattern, and the triage state machine that this repo now builds on.

This repo adapts those skills to a Gitea-centric workflow and composes them with the original orchestration skills (`app-design`, `ship-issue`, `milestone-builder`, `milestone-e2e-test`). See [`THIRD_PARTY_LICENSES.md`](./THIRD_PARTY_LICENSES.md) for the per-skill attribution table and full MIT license text.
