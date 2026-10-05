# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

A monorepo of agent **skills** in the open `SKILL.md` format — self-contained behavior packages an agent loads on demand — plus a Claude Code plugin layer (`.claude-plugin/`, `agents/`, `MODELS.md`). There is no build system, no test runner at the repo root, and no application to deploy. The artifacts are the skills themselves; editing a `SKILL.md` or a reference file *is* the deliverable.

Four companion docs at the repo root, each with a distinct audience:

- **`CONTEXT.md`** — meta-glossary for the skill set itself (Skill, Implementer, Reviewer, Main thread, Worktree, Milestone branch, Vault, etc.). **Read this before editing any SKILL.md.** The skills cross-reference each other; consistent terms are what keep composition from drifting.
- **`WORKFLOW.md`** — end-to-end developer manual for *using* the skill set (greenfield, brownfield, bug, UI redesign, triage flows). Point users here when they ask how the skills fit together.
- **`README.md`** — public-facing landing page. Skill index, three-layer overview, quick-reference table.
- **`MODELS.md`** — the role→model mapping for the execute-layer agent flows (which model plays Implementer, Reviewer, etc.) and the procedure for changing it. **When upgrading or reverting models, change `MODELS.md` first** — it lists every file that hard-names a model; prose everywhere else uses role names only.

## Layout

```
skills/<bucket>/<skill-name>/
  SKILL.md                 # required — YAML frontmatter + body
  references/*.md          # optional — load only the one you need at runtime
  scripts/                 # optional — executable helpers (Python stdlib preferred)
```

Utility agent definitions live at the repo root in `agents/<name>.md` (frontmatter `name`/`description`/`model`/`tools` + system prompt) and are listed explicitly in `.claude-plugin/plugin.json` under `agents`, so the runtime loads only the listed agents. `claude plugin validate` still warns that `agents/README.md` has no frontmatter and that the root `CLAUDE.md` isn't loaded as plugin context; both warnings are expected, and the README stays where it is.

Buckets: `language/`, `plan/`, `execute/`, `general/` — see each bucket's `README.md` for membership and [`WORKFLOW.md`](./WORKFLOW.md) for the three-layer model.

Each skill stands alone. Cross-skill references go through documented wikilinks (e.g., `[[grill-with-docs]]`, `[[language/improve-codebase-architecture/references/LANGUAGE.md]]`) or by the orchestrator skill spawning a sub-agent — never by importing files across skill boundaries.

## SKILL.md conventions

The frontmatter `description` is how Claude Code decides whether to invoke the skill. It must:
- List concrete trigger phrases the user is likely to say.
- Spell out when *not* to use the skill if there's a near neighbor.
- Stand alone — Claude only sees the description at routing time, not the body.
- Be a **single-line, double-quoted** YAML string — never a `|`/`>` block scalar. The docs only ever show single-line descriptions, and quoting is what keeps embedded colons (e.g. `MANDATORY TRIGGERS:`) and inner quotes from breaking the parse — an unquoted value containing `: ` is invalid YAML.

Body conventions:
- Use vocabulary from `CONTEXT.md` exactly. If a SKILL.md needs a term not in the meta-glossary, add it to `CONTEXT.md` first.
- `## Phase` / `## Step` headings drive multi-stage skills; gates between phases are explicit.
- Heavy content goes in `references/<topic>.md`. SKILL.md tells Claude when to load each reference; do **not** front-load everything into SKILL.md.
- IDs across documents (`[V-NNN]`, `[AC-NNN]`, `[S-NNN]`, `[D-NNN]`, `[SCR-NNN]`) are permanent — never renumber or reuse them, even across reworks.

When adding a new skill:
- Place it under `skills/<bucket>/<name>/` (pick the bucket that matches its layer: `language/`, `plan/`, `execute/`, or `general/`) with at minimum a `SKILL.md`.
- Add a row to the bucket's `README.md`, the skill index in the root `README.md`, and a line in `WORKFLOW.md`'s "Which skill for which situation" table.
- Add the new skill's path to `.claude-plugin/plugin.json`.
- Record its provenance in `THIRD_PARTY_LICENSES.md` — either a row in the "adapted from" table (if ported) or a line in the "Skills original to this repo" list.
- If the skill introduces a load-bearing term, add it to `CONTEXT.md` (with `_Avoid_:` aliases) before referencing it elsewhere.

When adding a new Utility agent: create `agents/<name>.md`, add its path to the `agents` array in `.claude-plugin/plugin.json`, add a row to `agents/README.md` and the root `README.md` table, and keep its `model:` consistent with the Utility agent row in `MODELS.md`. Search-type agents must end their report with the `confidence: found | partial | not-found` line so the Escalation ladder in `agents/README.md` works; callers key on that exact line.

## Skills that compose

The skills break into three layers — see `WORKFLOW.md` at the repo root for the end-to-end manual.

**Language layer** — the contract every other skill reads from:
- `grill-with-docs` — sharpen vocabulary; author `CONTEXT.md` and `docs/adr/` in the repo
- `improve-codebase-architecture` — surface deepening opportunities; uses the same vocabulary

**Plan layer** — turn intent into structured work:
- `app-design` — heavy 8-phase funnel for greenfield apps and major brownfield expansions
- `to-prd` — lightweight: synthesize current context into a single PRD on the tracker
- `to-issues` — slice a PRD/plan into independently-grabbable vertical-slice issues
- `triage` — state-machine gate (`needs-triage` → `ready-for-agent` etc.) that ship-issue and milestone-builder expect

**Execute layer** — the Main thread orchestrates and reviews on the strongest judgment model, a cheaper-context executor implements, and Utility agents in `agents/` handle commits, CI-log reading, test runs, tracker fetches, and Review packet assembly on the cheapest capable model (current mapping in `MODELS.md`):
- `ship-issue` — single issue, end-to-end (implement → CI → review → merge)
- `review` — the Reviewer's procedure; consumes a Review packet from the `review-prep` Utility agent, returns a report ending in a `verdict:` line that Stage 4 of the two flows above keys on
- `milestone-builder` — fans `ship-issue`-style flow across an entire milestone in dependency order
- `milestone-e2e-test` — browser-based validation step; routes non-trivial bugs through `/diagnose`
- `tdd` — red-green-refactor discipline invoked from implementer briefs
- `diagnose` — feedback-loop-first bug diagnosis discipline

**Vault vs. repo split** (load-bearing): the Obsidian vault holds *thinking-time* artifacts (vision, AC, wireframes, stories, design review). The repo holds *living* artifacts (`CONTEXT.md`, `docs/adr/`, architecture reviews). `CONTEXT.md` is born in the vault during app-design Phase 1–2, then moves to the repo at Phase 4.

When editing any of these, remember the contracts with the others: issue markdown shape, label conventions, dependency notation in issue bodies, the `CONTEXT.md` + ADR reading discipline in implementer/reviewer briefs.

## The app-design validator

`skills/plan/app-design/scripts/validate.py` is the main executable in the repo (the `har` skill's `scripts/` holds the only other two, also stdlib Python). Python 3.11+, stdlib only. Run it against a design project directory (an Obsidian folder, not this repo):

```
python skills/plan/app-design/scripts/validate.py all <project-path>
python skills/plan/app-design/scripts/validate.py traceability <project-path>
python skills/plan/app-design/scripts/validate.py ujt-coverage <project-path>                       # opt-in
python skills/plan/app-design/scripts/validate.py vocab <project-path> --repo <repo-path>           # opt-in
```

Exit code is the number of failures; `0` is PASS. Phase 7 of the app-design skill treats any non-zero exit as an automatic Blocker. If you change the validator, also update `skills/plan/app-design/scripts/README.md` — the README documents the canonical-definition-locations table and reference-only globs that callers depend on.

When changing definition/reference detection, mind the distinction in `scripts/README.md` ("Definition vs reference" section): a bracketed ID counts as a *definition* only when the bracket sits immediately after a heading/list/callout marker, optionally inside bold/italic, and the file matches the canonical glob for that prefix. Everywhere else it's a reference.

## Working in this repo

- Edits to a skill are immediately live for the next Claude Code session that loads it — there's nothing to compile or restart.
- The repo is public on GitHub at `chrisbalmer/ai-tools`. Changes land as pull requests against `main`; there is no CI, so check links and manifests by hand (see "When adding a new skill" above). The execute skills' flows are Gitea-first, so `/ship-issue` isn't used on this repo itself.
- Don't add a top-level package manager, lockfile, or CI config without checking — the repo intentionally has no build surface.
- When making changes that span multiple skills (e.g., adjusting a contract between `ship-issue` and `milestone-builder`), update both, plus `WORKFLOW.md` if user-facing, plus `CONTEXT.md` if vocabulary shifted. The cross-skill contract is the thing that breaks if you only edit one side.
