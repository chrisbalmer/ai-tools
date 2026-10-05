# Phase 8: Issue Creation

## Purpose
Generate implementation-ready issue files from the approved stories. These are structured for direct use in Gitea or GitHub, and are the handoff point to a coding skill or human developer.

## Vocabulary contract

Every issue body **must** use the vocabulary defined in the repo's `CONTEXT.md`. The implementer agent reads `CONTEXT.md` first; if your issue body uses a different word than the glossary does, the implementer will either (a) introduce a code identifier that drifts from the design or (b) ask a question that should have been resolved during Phase 2.

Before generating any issue file, re-read `<repo>/CONTEXT.md`. If a story still uses a fuzzy term, stop and resolve it — either add the term to `CONTEXT.md`, or rewrite the story to use the existing canonical term. This is the same discipline as [[grill-with-docs]] but applied to issue bodies instead of conversation.

The validator (`scripts/validate.py vocab`) flags issue bodies that use terms not present in `CONTEXT.md` and not obviously common English. Run it before declaring Phase 8 done.

## Issue Format

One markdown file per story. The file is structured so it can be pasted directly into a Gitea/GitHub issue body, or imported programmatically.

## Filename Convention

Issue files use a build-order prefix so the directory sorts in build order:

```
{ProjectName}/Issues/{NN} - {S-NNN} - {ShortTitle}.md
```

Where `{NN}` is the **two-digit zero-padded build-order position** from the Phase 6 Dependency Graph and `{S-NNN}` is the story ID. Example sequence:

```
01 - S-097 - AppSettings Schema Migration.md
02 - S-099 - IAP Module Skeleton.md
03 - S-098 - ProFeatureRegistry Skeleton.md
...
```

Rationale: alphabetical filename sort = build order. An implementer can walk the directory in order and ship issues sequentially without consulting a separate ordering document. The Gitea/GitHub issue counter assigned at import time is independent of this prefix — the prefix is purely for local file ordering and traceability. The issue *title* in the upstream tracker stays `[S-NNN] {Story Title}` per the existing convention; the build-order prefix lives only in the markdown filename.

For promotion cycles, suffix the `Issues/` directory: `Issues - v2.0/`, `Issues - v2.1/`, etc. The `{NN}` numbering restarts within each cycle's directory.

## Output: `{ProjectName}/Issues/{NN} - {S-NNN} - {ShortTitle}.md`

```markdown
---
tags:
  - {project-tag}
  - issue
  - {epic-tag}
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} Issue S-{NNN}
---

## Title

[S-NNN] {Story Title}

## Description

{Context from the vision and architecture. What this story is building and why. Include enough context that the Implementer (or a human) can understand the purpose without reading every other design document — capped at two short paragraphs; reference IDs ([V-NNN], [AC-NNN]) instead of restating their documents.}

## Acceptance Criteria

{Copied from the relevant [AC-NNN] entries, filtered to what this specific story covers. Include the "It should" and "How we prove it" sections. Keep "It should not break" if there are non-obvious regression risks.}

## Technical Notes

{Relevant architecture decisions, data model details, API boundaries, or cross-cutting concern implementations from Phase 4. Only include what's directly relevant to this story — don't dump the whole architecture doc.}

## Screen Reference

{If this story builds or modifies a screen, reference [SCR-NNN] and summarize the wireframe layout and key elements. Optional for backend-only stories.}

## Comp Reference

{If this story touches UI, reference the Comp files in the Design bundle for each [SCR-NNN] the story renders. The Comp is the visual source of truth — the Implementer `Read`s it, and the Reviewer diffs the running app against it (Visual diff gate). Example:}

- `[SCR-003]` Book Detail — `design_handoff_<project>/screenshots/03-book-detail.png`
- `[SCR-003-empty]` Book Detail (empty state) — `design_handoff_<project>/screenshots/03-book-detail-empty.png`

{For backend-only stories: omit this section or write `Headless — no Comp reference`.}

## Files Likely Touched

{From the story's "Files likely touched" field — helps scope the work}

## UJTs to Translate

{From the story's "Done when" UJT IDs. List each UJT ID and its one-line title; include the source path so the implementer can read the prose without grepping. Example:}

- `[UJT-007]` Add Book — minimum fields (happy path) — see `User Journey Tests/Books and Shelves.md`
- `[UJT-007-a]` Add Book — cancel mid-entry — see `User Journey Tests/Books and Shelves.md`
- `[UJT-007-b]` Add Book — validation: missing required fields — see `User Journey Tests/Books and Shelves.md`

**Done means:** the implementer translates each UJT to a runnable form (XCUITest method, Playwright spec, manual smoke walk-through, etc.) in the same PR as the production code, and all listed UJTs pass. If translating a UJT surfaces design drift, file the drift as a separate issue and adjust the UJT or AC to match reality before merging. See [[phase-5-stories.md#the-implementer-side-cycle]].

For headless stories (backend-only, CLI, pipeline) the story's "Done when" should describe the verifying test directly; this section can read `Headless — no UJTs; verified by {test target}`.

## Dependencies

**Blocked by:** {List of [S-NNN] issues that must be completed first, with their short titles, or "None"}
**Blocks:** {List of [S-NNN] issues that depend on this one, or "None"}

## Labels

- `epic:{epic-name}`
- `phase:{build-phase-number}`
- `scope:mvp`
```

## Batch Presentation

Don't dump all issues at once. Present them grouped by build phase:

1. Show Build Phase 1 issues first
2. Ask for approval
3. Continue through each build phase

This lets the user catch problems early without reviewing 30 issues at once.

## Issue Numbering

Three separate numbers, none of which should be conflated:

- **Build-order prefix `{NN}`** — Position in the build sequence from Phase 6. Only used in the local markdown filename. Resets per promotion cycle.
- **Story ID `[S-NNN]`** — Permanent identifier from Phase 5. Appears in the filename, the issue title, and every trace.
- **Upstream issue number** — Assigned by Gitea/GitHub at import time from the upstream counter. Not visible in the Design bundle.

The build-order prefix and the story ID together fully identify a file. The upstream issue number is recorded back into the Design bundle only if the user wants it (e.g., as a frontmatter `gitea_issue: 142` field).

## Foundation Slice (slice 0)

For UI projects, the **first issue** in build order must be a Foundation slice that extracts the visual language from the Comps into code: design tokens (colors, typography, spacing), shared layout components (nav shell, card patterns, form styles), and base CSS/theme setup. This slice:

- Lists the Design bundle directory path in **Technical Notes** as extraction source material (not in `## Comp Reference` — the Foundation slice renders no complete screens, so the Visual diff gate should not fire). Its `## Comp Reference` should read `Foundation — no screen rendering; Comps consumed as extraction source`.
- Has no blockers (it's the root of the UI dependency graph)
- Blocks every subsequent slice that renders UI
- Is AFK — an Implementer can extract tokens from the Comps without human judgment

The Foundation slice is what prevents N parallel Implementers from each independently inventing colors, spacing, and component shapes. Without it, visual consistency across slices is accidental.

## Gate

Ask per build phase: "Here are the issues for Build Phase N. Ready to approve these?"

After all phases are approved: "All issues are ready. The design phase is complete. These can be picked up by a coding workflow, imported into Gitea/GitHub, or worked manually."

## What Happens Next

The design skill's job ends here. The user can:
- Import issues into Gitea or GitHub (manually or via API)
- Hand them to a coding skill that picks up issues and implements them
- Work them manually as a developer
- Come back to this skill later to add `v2` features (re-enter at Phase 2 to promote criteria, then cascade through)

**Handoff contract for the execute layer.** The issue bodies above are written in design-package terms and are NOT yet what `/ship-issue` and `/milestone-builder` consume. On import, two rewrites are required:

1. **Dependencies** — the `**Blocked by:** [S-NNN]` / `**Blocks:** [S-NNN]` entries must be rewritten to tracker issue numbers (`**Blocked by:** #7, #15`) once upstream numbers exist. `/milestone-builder` parses `#N` from the `## Dependencies` section; story IDs there are invisible to it.
2. **Triage state** — the Labels list carries no triage label, and both execute skills refuse issues that aren't `ready-for-agent`. Route imported issues through [[triage]] (usually a fast pass, since the design package already answers the brief's questions).

Both rewrites happen automatically when the issues go through `/to-issues`; only the direct-import path has to do them by hand.
