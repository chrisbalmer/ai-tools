# ai-tools

A monorepo of agent skills (open `SKILL.md` format) with a Claude Code plugin layer. This `CONTEXT.md` pins the vocabulary the skills themselves use, so cross-skill references stay consistent. The skills compose, and composition is what compounds drift if the terms aren't fixed.

For the *format* of a CONTEXT.md in a downstream project, see `skills/language/grill-with-docs/references/CONTEXT-FORMAT.md`. For the *architecture* vocabulary used inside the `/improve-codebase-architecture` skill, see `skills/language/improve-codebase-architecture/references/LANGUAGE.md`. This file is for the skill set's own meta-vocabulary.

## Language

### Skills and structure

**Skill**:
A self-contained behavior package under `skills/<bucket>/<name>/`. Each Skill has exactly one `SKILL.md` (entry point) and zero or more `references/` files (loaded on demand).
_Avoid_: subagent (that's a different thing — see below), command, plugin.

**SKILL.md**:
The frontmatter + body file at the root of a Skill. The frontmatter description is what Claude Code routes against; the body is what gets loaded once the Skill is invoked.
_Avoid_: manifest, spec.

**Reference**:
A markdown file under a Skill's `references/` directory that the `SKILL.md` tells Claude to load on demand. References hold heavy content that doesn't belong in `SKILL.md`.
_Avoid_: doc, ref file, extra (too vague).

### Agent roles in the execution layer

Role→model assignments live in `MODELS.md` at the repo root. Prose throughout the skills refers to these role names, never to model names — outside `MODELS.md`, models are named only in the `model:` fields of the Agent-call examples in the two execute skills, the frontmatter `model:` of each Utility agent in `agents/`, and in the _Avoid_ alias lists below (which exist to ban model-flavored names and don't churn with the mapping).

**Main thread**:
The session the user is actively interacting with, run on the strongest judgment model available (see `MODELS.md`). Holds the cross-cutting context (issue body, spec, in-flight branches, dependency graph). Briefs Subagents and arbitrates their output.
_Avoid_: orchestrator, main session, parent agent.

**Subagent**:
An `Agent`-tool-spawned session, isolated from the Main thread, used for a single well-scoped task. Two flavors: **Implementer** and **Reviewer**.

**Implementer**:
A Subagent (model per `MODELS.md`) spawned in an isolated git worktree to write code against a single Issue's brief. Opens a PR; does not merge. Used by `/ship-issue` and `/milestone-builder`.
_Avoid_: opus agent, opus implementer, sonnet implementer, implementer subagent — collapse all to **Implementer**.

**Reviewer**:
A Subagent (read-only, no worktree; model per `MODELS.md`) that reads a PR's diff from a Review packet, runs the `/review` skill's procedure, and returns a structured review ending in a `verdict:` line. Used by `/ship-issue` and `/milestone-builder`.
_Avoid_: fable reviewer, opus reviewer, review subagent — collapse to **Reviewer**.

**Fix agent**:
A Subagent (model per `MODELS.md`) spawned to address a specific Reviewer finding when the fix is larger than ~50 LOC of inline mechanical edit. Briefed similarly to an Implementer but scoped to the specific finding.
_Avoid_: fix subagent, opus fix agent, sonnet fix agent.

**Inline fix**:
A small mechanical edit (under ~50 LOC) made directly on the Main thread in the Implementer's preserved worktree, rather than spawning a Fix agent. Used for lint nits, dead code, doc typos.
_Avoid_: hot fix (overloaded with prod-fix meaning).

**Utility agent**:
A Subagent run on the cheapest capable model (the Utility-agent tier in `MODELS.md`) for a mechanical, well-bounded chore whose *output* is bulky but whose *judgment* is trivial: committing, reading CI logs, running a test suite, fetching tracker issues. Defined once as agent files under `agents/` in this plugin (`commit`, `ci-check`, `test-run`, `tracker-read`, `review-prep`); the Main thread delegates to them so orchestrator-tier context isn't spent on diff, log, and issue-body dumps. Writes no application code (not an Implementer) and renders no verdict (not a Reviewer).
_Avoid_: helper agent, haiku agent, chore agent, utility subagent.

**Review packet**:
The digest plus on-disk scratch files (`diff.patch`, `diff-generated.patch`, `packet.md`, optional `shots/*.png`) that the `review-prep` Utility agent assembles for a Reviewer: changed-file table by role, new identifiers checked against `CONTEXT.md` terms and `_Avoid_` aliases, ADR hits for the touched area, tests added and AC IDs referenced, migration presence, PR hygiene. The Reviewer reads the diff from the packet instead of fetching it; the Main thread keeps only the digest. Facts only — the packet renders no verdict.
_Avoid_: review context, prep report, diff digest, review bundle (collides with Design bundle).

**Escalation**:
Re-spawning the *same* Utility-agent brief once on the next model tier up (the Escalation tier in `MODELS.md`) after the agent reports `confidence: partial` or `not-found`; if the retry also fails, the Main thread does the work itself. Escalation is per-brief and reactive — never a raised default, never pre-emptive because a task "looks hard".
_Avoid_: retry on a bigger model, upgrade the agent, bump the model.

### Git topology

**Worktree**:
An isolated git checkout used by an Implementer. Created via `Agent` tool's `isolation: "worktree"`. Preserved after the Implementer completes so the Main thread can apply Inline fixes there.

**Milestone branch**:
The shared branch (`milestone-<ID>-<kebab-name>`) created from main at the start of a `/milestone-builder` run. All Issue branches in the milestone target this branch.

**Issue branch**:
A short-lived branch created in an Implementer's Worktree, named `issue-<N>-<short-description>` or `feat/<N>-<slug>`. Targets the Milestone branch (in `/milestone-builder` flow) or main directly (in `/ship-issue` flow).

**Milestone PR**:
The single PR from the Milestone branch to main, opened after every Issue in the milestone has merged into the Milestone branch. Left open for human review. Distinct from individual **Issue PRs** which target the Milestone branch.

### Work units

**Issue**:
A single tracked unit of work on the Gitea tracker. Carries one **Category role** (`bug` or `enhancement`) and one **State role** (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`).
_Avoid_: ticket (use only when quoting external tools that call them tickets).

**Triage role**:
A canonical label name applied to an Issue. Mapped to the actual Gitea label string via the per-repo mapping in that repo's `MEMORY.md`.

**Vertical slice** *(synonym: tracer bullet)*:
An Issue whose scope cuts through every relevant layer (schema, API, UI, tests) end-to-end. Demoable on completion. The default Issue shape from `/to-issues`. Contrast with the rejected **horizontal slice** ("schema PR, then API PR, then UI PR"), which produces nothing demoable until the last layer lands.

**AFK**:
An Issue an Implementer can ship without human interaction. Default; prefer AFK over HITL.

**HITL** (human-in-the-loop):
An Issue requiring human judgment mid-flow (architectural decision, design review, manual test the Implementer can't run). Used sparingly.

**Tier**:
A set of Issues in a milestone whose dependencies are all satisfied and can ship in parallel. `/milestone-builder` spawns one Implementer per Issue in a Tier in a single turn.

### Design artifacts

**Vault**:
The user's Obsidian vault (written `<vault>/` in examples; its location is per-user). Holds *thinking-time* artifacts from `/app-design`: Vision, Acceptance Criteria, Wireframes, Stories, Dependency Graph, Design Review.

**Repo**:
The project's code repository. Holds *living* artifacts: `CONTEXT.md` (the project's domain glossary, not this file), `docs/adr/`, architecture review reports, and the **Design bundle** (`design_handoff_<project>/`).

**CONTEXT.md**:
The domain glossary at a project repo's root. Format defined in `skills/language/grill-with-docs/references/CONTEXT-FORMAT.md`. Implementers and Reviewers read it on every PR. Different from *this* file, which is the meta-glossary for the skill set itself.

**ADR** (Architecture Decision Record):
A `docs/adr/0NNN-<slug>.md` file capturing a hard-to-reverse, surprising, trade-off decision. Format defined in `skills/language/grill-with-docs/references/ADR-FORMAT.md`.

**UJT** (User Journey Test):
An end-to-end test spec written in prose during `/app-design` Phase 5, alongside Stories. Stored under `<Vault>/<Project>/User Journey Tests/`. Translated to runnable form (XCUITest, Playwright, etc.) by the Implementer when the Issue body lists `## UJTs to Translate`.

**AC** (Acceptance Criterion):
A `[AC-NNN]`-tagged contract written during `/app-design` Phase 2. Carries a scope tag (`mvp`, `v2`, `future`).

**Story**:
A `[S-NNN]`-tagged work unit written during `/app-design` Phase 5. Traces to one or more ACs. Becomes the basis for an Issue at Phase 8.

### Feedback discipline

**Feedback loop**:
A fast, deterministic, agent-runnable pass/fail signal. The core artifact of `/diagnose` Phase 1. Everything else in `/diagnose` (bisection, hypothesis testing, instrumentation) just consumes this signal.
_Avoid_: repro (too narrow — a Feedback loop is *more* than a repro, it's an automated one).

**Deepening**:
A refactor that turns a shallow module into a deep one — more behavior behind a smaller interface. The output of `/improve-codebase-architecture`. Vocabulary defined fully in `skills/language/improve-codebase-architecture/references/LANGUAGE.md`.

**Agent brief**:
A structured comment posted on an Issue when it moves to `ready-for-agent`. The authoritative spec the Implementer works from. Format defined in `skills/plan/triage/references/AGENT-BRIEF.md`.

**Foundation PR**:
A PR that lands only docs/conventions (`CONTEXT.md`, `docs/adr/`, `CLAUDE.md`, `MEMORY.md`) with no code changes. Used when retrofitting a long-lived repo with these conventions.

**Comp**:
A high-fidelity rendered visual of a specific screen (`[SCR-NNN]`), produced during `/app-design` Phase 3 as part of the Design bundle. Includes screenshot PNGs (the visual target Implementers match and Reviewers diff against) and prototype HTML/JSX source (the token and structure reference). Lives in the repo, not the vault — Implementers and Reviewers `Read` these files directly from their worktrees.
_Avoid_: mockup (too casual — doesn't convey SoT status), prototype (overloaded with throwaway-code meaning — the `prototype/` directory in the bundle holds the Comp source, but "prototype" alone implies disposable code).

**Design bundle**:
A directory in the repo (`design_handoff_<project>/`) containing the design-to-implementation handoff: prototype HTML/JSX, numbered screenshots, spec README, and supporting docs (art style guide, architecture). Produced during `/app-design` Phase 3 and refined through Phase 7. The Comps inside the bundle are the visual SoT for every screen. Lives in the repo so Implementer and Reviewer agents can `Read` it from their worktrees.
_Avoid_: design package (ambiguous with npm packages), design system (that's the extracted tokens/components, not the artifact set).

**Visual diff gate**:
The Reviewer's step of comparing a screenshot of the rendered app against the Comp for each screen the PR touches. The gate that prevents implementers from rebuilding a screen from textual specs alone, which silently diverges from the approved visual. Part of Stage 3 (Review) in `/ship-issue` and `/milestone-builder`.
_Avoid_: design review (overloaded with Phase 7), visual QA (too informal).

**Foundation slice** *(synonym: slice 0)*:
The first vertical slice in a UI project, extracted from the Comp during `/to-issues` or `/app-design` Phase 8. Lands the design tokens (colors, typography, spacing), shared layout components, and base styles that every subsequent UI-touching slice depends on. Has no blockers; blocks every slice that renders UI.
_Avoid_: setup issue, scaffolding ticket (too vague — this is specifically about extracting the Comp's visual language into code).

### Evidence artifacts

**Capture**:
A browser HAR export of a web UI session, recorded to learn the *real* request a vendor UI makes for an action. Exists in two states — **raw** (contains cookies, tokens, tenant PII; never read into a conversation, never committed) and **sanitized** (produced by `/har`'s `scripts/sanitize-har.py`; safe to digest and attach, still contains tenant *content*). A Capture is evidence for the project's **Observed-API doc** and the source of a **Fixture**; it is not itself a deliverable.
_Avoid_: HAR dump, network log (too generic), trace (overloaded with distributed tracing).

**Observed-API doc**:
The project-repo document (e.g. `docs/api/<platform>-observed.md`) that records endpoints, shapes, and semantics *as actually observed* from Captures and live runs, as opposed to inferred from vendor docs. The source of truth for a client adapter; corrected whenever a Capture contradicts it.
_Avoid_: API spec (implies vendor-authored), swagger.

**Fixture**:
A sanitized JSON body extracted from a Capture (via `/har` `extract`) and stored under the project's fixtures path (e.g. `docs/api/*.json`, mirrored into the test bundle). What contract tests decode against.
_Avoid_: sample data, mock response (a mock is hand-written; a Fixture is captured).

## Relationships

- A **Skill** has one `SKILL.md` and zero or more **References**
- A **Capture** (sanitized) yields **Fixtures** and corrections to the **Observed-API doc**; the raw Capture yields nothing directly and is never read
- The **Main thread** spawns many **Subagents**; each is either an **Implementer**, a **Reviewer**, or a **Fix agent**
- An **Issue** carries one **Category role** and one **State role**
- A **Milestone** holds many **Issues** organized into **Tiers**
- Each **Issue** produces one **Issue PR** targeting the **Milestone branch**
- All **Issue PRs** merging into the **Milestone branch** roll up to one **Milestone PR** targeting main
- An **Implementer** reads `CONTEXT.md`, relevant **ADRs**, and the **Agent brief** on the Issue
- A **Reviewer** reads the same plus the Implementer's flagged judgment calls and the **Review packet** assembled by the `review-prep` **Utility agent**
- `/app-design` produces **Vision** → **ACs** → **Wireframes** + **Comps** → **Architecture** → **Stories** + **UJTs** → **Dependency Graph** → **Design Review** → **Issues**
- A **Comp** is the rendered visual of a **Screen** (`[SCR-NNN]`); Implementers match it, Reviewers diff against it (**Visual diff gate**)
- A **Foundation slice** extracts design tokens from the **Comps** before UI-touching slices begin

## Flagged ambiguities

- **"Implementer" vs. model-flavored names ("sonnet agent", "opus implementer") vs. "implementer subagent"** — resolved: all become **Implementer**. The model is an implementation detail that changes; `MODELS.md` pins the current assignment.
- **"Reviewer" vs. model-flavored names vs. "review subagent"** — resolved: **Reviewer**. Same reasoning.
- **"Main thread" vs. "orchestrator" vs. "main session"** — resolved: **Main thread**.
- **"Issue branch" vs. "feature branch" vs. "PR branch"** — resolved: **Issue branch** when in a milestone flow; the older `feat/<N>-<slug>` convention in `/ship-issue` standalone runs is still valid but should be renamed when documents are next touched.
- **"Repro" vs. "Feedback loop"** — resolved: **Feedback loop** for the automated signal from `/diagnose` Phase 1; "repro" is informal and not interchangeable.
- **"Skill" vs. "subagent"** — distinct: a **Skill** is a behavior package; a **Subagent** is a spawned Agent-tool session. A Subagent may invoke a Skill, but they are not the same thing.
