---
name: app-design
description: "Structured design phase for new applications and features. Guides the conversation from unconstrained vision through acceptance criteria, architecture, story decomposition, dependency mapping, and design review — producing Obsidian notes and diagrams at each phase. Use this skill whenever the user wants to plan, design, or architect a new app, feature set, or major project before coding. Triggers include 'design an app', 'plan a new project', 'let's architect', 'I want to build', 'app idea', 'new application', 'feature planning', 'design phase', or any request to think through what an application should be before writing code. Also use when the user wants to continue a design already in progress or re-enter at a specific phase. Do NOT use for a feature-shaped addition to an existing app that doesn't need the full 8-phase funnel — that's /to-prd."
---

# App Design Skill

Guide the user through a structured design funnel that starts with unconstrained vision and narrows to implementation-ready issues. Every phase produces Obsidian notes (following the [[obsidian-note]] skill conventions). No code is written during this process — the output is a complete set of design artifacts (vault notes, Design bundle, and issue files) that a coding skill or human developer can pick up.

## Core Principles

- **One phase at a time.** Never advance to the next phase without explicit user approval.
- **The user is the authority.** Present work for review, incorporate feedback, re-present. Don't rush gates.
- **Traceability.** Every story traces back to an acceptance criterion. Every acceptance criterion traces back to a vision feature. If something can't be traced, it's either missing upstream or shouldn't exist.
- **MVP discipline.** The full vision is captured, but only MVP-scoped work flows into architecture and beyond. Everything else is parked, not forgotten.
- **No code.** Pseudocode and interface signatures are fine for clarity. Actual implementation belongs to the coding phase.

## Quality discipline — lessons learned

Eight conventions that emerged from real design cycles — this is only the index; the named reference carries the full rule:

- **Bias-break on review** — Phase 7 runs in a fresh session, never the author of Phases 5/6; re-reviews of rework also get fresh verifiers (`phase-7-review.md`)
- **Multi-pass verification** — Blockers → rework → fresh re-verify, until PASS with zero Blockers (`phase-7-review.md`)
- **Computed expected values** — AC tests involving dates, times, or arithmetic get expected values *computed*, never intuited (`phase-2-acceptance-criteria.md`)
- **Code-vs-design re-sync** — when code exists, Phase 7 verifies the design's claims about the codebase against reality (`phase-7-review.md`)
- **Pre-edit audit for reworks** — before reworking a concept, list every artifact that mentions it (`promotion-cycle.md`)
- **User Journey Tests** — authored alongside stories in Phase 5; each story's done-when lists the UJTs that prove it (`user-journey-tests.md`)
- **Shared domain language travels with the code** — `CONTEXT.md` and `docs/adr/` live in the repo, not the vault (see "Vault vs. repo split" below and [[grill-with-docs]])
- **Comp as visual source of truth** — Phase 3 renders a Comp (prototype HTML/JSX + screenshots) for every MVP screen into a Design bundle (`design_handoff_<project>/`) committed to the repo; Implementers match it and Reviewers diff the running app against it in the Visual diff gate. A screen with no Comp means the bundle is incomplete — caught at Phase 7 (`phase-3-wireframes.md`)

A `scripts/validate.py` helper enforces traceability, ID uniqueness, orphan references, scope tags, and stray `M_NEXT` migration placeholders. The phase references say when to run it; failures at Phase 7 are automatic Blockers.

Invoke it with the absolute path to `validate.py` (e.g. `python <skill-dir>/scripts/validate.py all <project-path>`, where `<skill-dir>` is wherever the plugin or skill is installed). The script can be run from any working directory — only the `<project-path>` argument has to be correct, since the design project lives in the user's Obsidian vault, not in this skill's directory.

## Phase Overview

| Phase | Name | Gate | Key Output |
|-------|------|------|------------|
| 1 | Vision | User confirms the vision captures what they want | Vision document |
| 2 | Acceptance Criteria & MVP Scoping | User approves criteria and MVP/v2/future tags | Feature criteria notes with scope tags |
| 3 | Wireframes & Screen Inventory | User confirms screens and flows | Screen layouts + navigation diagram + rendered Comps |
| 4 | Architecture & Technical Design | User confirms technical approach | Architecture doc + diagrams |
| 5 | Story Decomposition | User agrees stories cover all MVP criteria | Story notes with traceability |
| 6 | Dependency Graph & Sequencing | User approves build order | Dependency diagram + sequence doc |
| 7 | Design Review | User gives final sign-off | Review checklist + issue-ready stories |
| 8 | Issue Creation | User confirms issues are correct | Gitea/GitHub issue markdown files |

Phase 3 (Wireframes) is optional for backend-only or headless projects. Ask the user if they want to skip it when there's no UI.

## How to Start

When the user triggers this skill, figure out where they are:

- **Starting fresh**: Begin at Phase 1. Ask them to describe their app idea or, if they haven't yet, prompt them with the Phase 1 opener.
- **Resuming**: If the conversation already contains design work (a vision statement, acceptance criteria, etc.), identify the latest completed phase and pick up at the next one. Confirm with the user: "It looks like we've completed through Phase N. Ready to move to Phase N+1?"
- **Re-entering at a specific phase**: If the user says "let's redo the architecture" or "start from acceptance criteria", jump to that phase. Warn them that downstream phases will need to be revisited.
- **Starting v2 / promoting features**: If MVP is built and the user wants to tackle `v2` or `future` items, read `references/promotion-cycle.md` and follow the promotion cycle.
- **Mid-build scope change**: If the user reports a gap or new requirement discovered during coding, read `references/promotion-cycle.md` and follow the mid-build scope change process.

> [!important] Resumption ≠ verification
> A session resuming at Phase N can do Phase N work. But if the *next* phase is 7 (Design Review), it does not run the review itself — it spawns a fresh independent session for that. The author of Phases 5/6 is biased toward confirming its own work. Same rule for re-reviews of rework: each rework iteration gets a fresh verifier, not the rework author.

### Greenfield vs. Brownfield

At the start, determine whether this is a new project or an addition to an existing one.

- **Greenfield**: Full process from Phase 1.
- **Brownfield** (adding features to an existing app): Phase 1 becomes "what are we adding?" rather than "describe the whole app." Phase 4 (Architecture) starts with documenting the current state before designing changes. Ask the user to point you at existing code, docs, or schemas if available.

## Phase Details

Each phase has its own reference file in `references/`. Read the relevant file before beginning a phase — only load the phase you're working on, not all of them.

| Phase | Reference File |
|-------|---------------|
| 1 | `references/phase-1-vision.md` |
| 2 | `references/phase-2-acceptance-criteria.md` |
| 3 | `references/phase-3-wireframes.md` |
| 4 | `references/phase-4-architecture.md` |
| 5 | `references/phase-5-stories.md` |
| 6 | `references/phase-6-dependencies.md` |
| 7 | `references/phase-7-review.md` |
| 8 | `references/phase-8-issues.md` |
| — | `references/promotion-cycle.md` |

## Beyond MVP

The 8-phase process produces MVP issues. After MVP ships (or during build if new requirements surface), the skill supports two additional workflows documented in `references/promotion-cycle.md`:

- **Promotion cycle**: Lightweight pass through the phases to move `v2` or `future` criteria into active development. Starts with a retrospective, then updates existing design documents rather than creating new ones. Read this reference when the user says "let's start on v2" or wants to promote features.
- **Mid-build scope change**: Handles requirements discovered during implementation. Ranges from minor inline tweaks to moderate design passes, with a severity assessment to pick the right level of process. Read this reference when the user reports a gap found during coding.

## Output Conventions

All notes follow the obsidian-note skill format:
- Frontmatter with tags, created date, aliases
- No `#` heading (filename is the title)
- Sections start at `##`
- Use Obsidian callouts, wikilinks, and code blocks where appropriate

### Vault vs. repo split

Two storage locations, two roles:

- **Obsidian vault** — *thinking-time* artifacts produced during design phases: vision, acceptance criteria, wireframes, story decomposition, dependency graph, design review. Frozen design-time record.
- **Project repo** — *living* artifacts that the code and the agents reading the code depend on: `CONTEXT.md` (glossary), `docs/adr/` (decisions), architecture review reports. These travel with the code.

`CONTEXT.md` is **born in the vault** during Phase 1 (vision) as terms emerge. The moment the repo is created — typically Phase 4 when tech stack is locked in — **copy `CONTEXT.md` to the repo root** and stop editing the vault copy. ADRs follow the same rule. From that point on, every implementer agent (`/ship-issue`, `/milestone-builder`) reads from the repo and updates the repo copy when introducing new vocabulary.

For brownfield projects, the repo already exists. Read `CONTEXT.md` and `docs/adr/` at the start of Phase 1; never duplicate them into the vault.

### Project Directory

At the start of Phase 1, ask the user two things:
1. **Project name** (or infer from context and confirm)
2. **Where to place the project directory** — e.g., "Where in your vault should I put the {ProjectName} folder?"

All design artifacts live inside that directory:

```
{base-path}/{ProjectName}/
  Vision.md
  Acceptance Criteria/
    {FeatureName}.md
  Wireframes.md
  Architecture.md
  Stories/
    {EpicName}.md
  User Journey Tests/
    {JourneyName}.md
  Dependency Graph.md
  Design Review.md
  Issues/
    Issue {NNN} - {ShortTitle}.md
```

`User Journey Tests/` is opt-in: present on UI-bearing projects, absent on headless ones. See `references/user-journey-tests.md`.

The project directory is the namespace — individual files don't need the project name repeated in them. Keep filenames short and descriptive.

### Diagrams

Use Mermaid blocks inside Obsidian notes for:
- Entity-relationship diagrams (data model)
- Flowcharts (user flows, decision trees, navigation)
- Sequence diagrams (API interactions, component communication)
- Gantt charts (build sequencing)

Use SVG (via the Visualizer) for:
- Wireframe layouts where spatial positioning matters
- Component boundary maps where Mermaid auto-layout is confusing
- System architecture overviews that benefit from custom positioning

When using Mermaid in Obsidian notes, wrap in a fenced code block with the `mermaid` language tag.

### Traceability Tags

Throughout the design, use a consistent tagging scheme so everything traces back:

- Vision features: `[V-001]`, `[V-002]`, etc.
- Acceptance criteria: `[AC-001]`, `[AC-002]`, etc.
- Screens: `[SCR-001]`, `[SCR-002]`, etc.
- Stories: `[S-001]`, `[S-002]`, etc.

Every acceptance criterion references the vision feature(s) it satisfies. Every story references the acceptance criteria it implements. The design review verifies this chain is complete.

**IDs are permanent.** Never renumber or reuse an ID, even when adding features later or re-entering a phase. New additions get the next available number in their sequence. This keeps references stable across all documents.

## Handoff to Coding

Phase 8 produces issue markdown files structured for direct import to Gitea or GitHub. Each issue contains:
- Title
- Description with context
- Acceptance criteria (copied from the traced AC)
- Dependencies (which issues must be completed first)
- Labels/tags suggestion

This is the contract the coding phase works from. A separate coding skill can pick up these issues and implement them. The design skill's job ends when the user approves the issues.
