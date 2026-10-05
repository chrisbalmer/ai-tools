# Phase 5: Story Decomposition

## Purpose
Break each MVP acceptance criterion into implementable stories. Each story should be a well-scoped unit of work that can be completed in a single Claude Code session — or a single focused human coding session as a fallback.

## Scope
Only decompose `mvp`-tagged acceptance criteria. If a `v2` or `future` criterion is needed as a dependency for an MVP story, flag it and discuss with the user — they may need to promote it to MVP.

## Sizing: Claude Code Primary

Stories are primarily sized for Claude Code working from a Gitea/GitHub issue. A well-sized story for Claude Code:

**Right-sized:**
- Touches 1-3 files substantially (Claude Code holds context well within this range)
- Has a clear, testable end state describable in 2-3 sentences
- Doesn't require understanding the full codebase — just the relevant slice
- Can be verified with a specific test or observable behavior
- Either frontend or backend, not both (split across the boundary)

**Too big:**
- Requires context across 5+ files to understand what to change
- Mixes concerns: API + database + frontend in one story
- Has the word "and" connecting two unrelated behaviors
- Would need Claude Code to make architectural decisions (those belong in this design phase)
- Produces changes that can't be tested in isolation

**Too small:**
- Just creates an empty file or boilerplate with no logic
- Is a single-line config change
- Can't be meaningfully verified

> [!note] Human Fallback
> If a human is implementing instead of Claude Code, the same sizing guidance applies — a well-scoped story is a well-scoped story. The only difference: a human might combine 2-3 very small Claude Code stories into one sitting. The issue granularity stays the same either way.

## Story Structure

Each story gets an ID `[S-NNN]` and traces back to one or more acceptance criteria.

## Output: `{ProjectName}/Stories/{EpicName}.md`

Group stories by epic (which roughly maps to feature areas from Phase 2).

```markdown
---
tags:
  - {project-tag}
  - design
  - stories
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} Stories {EpicName}
---

## Epic: {Feature Area Name}

Implements: [V-NNN] {Vision Feature}

### [S-001] {Story Title}

**Traces to:** [AC-NNN], [AC-NNN]
**Screen:** [SCR-NNN] (if applicable)

**Description:**
{What this story delivers. Be specific about inputs, outputs, and behavior.}

**Done when:**
{Concrete completion criteria — what can be demonstrated or tested}

**Files likely touched:**
{Best guess at which files/modules this changes — helps Claude Code scope its context}

**Notes:**
{Implementation hints, edge cases to watch for, or constraints. Optional.}

### [S-002] {Story Title}
{...same structure}
```

The "Files likely touched" field is a best guess based on the architecture from Phase 4. It helps Claude Code (or a human) scope their work before starting. It's not a contract — if the implementation needs to touch other files, that's fine.

## Traceability Check

After decomposing all stories, build a traceability matrix:
- Every `mvp`-tagged `[AC-NNN]` must be covered by at least one `[S-NNN]`
- Every `[SCR-NNN]` from Phase 3 should have stories that build it
- Flag any acceptance criteria with no stories (gap)
- Flag any stories that don't trace to an acceptance criterion (scope creep)

Present the matrix to the user.

## Authoring UJTs

Stories are paired with User Journey Tests (UJTs) — the journey-form definition of done. See [[user-journey-tests.md]] for the four-primitive DSL (`STEP`, `EXPECT`, `INPUT`, `STATE`), file structure, and execution modes.

> [!important] UJTs are the acceptance contract, not an afterthought
> For every UI-bearing story in a UI project, the story **must** list at least one UJT ID in its "Done when" field. The UJT is what the implementer translates to executable form (e.g. XCUITest) in the implementation PR; "implementation done" means "UJT-translated test exists, runs, and is green." A story without a UJT is a story without a runnable acceptance contract — fix that here, in Phase 5, not after the implementer is already shipping code.

For each story, in the same Phase 5 sitting:

1. Sketch the happy-path UJT (`[UJT-NNN]`) under `{ProjectName}/User Journey Tests/`.
2. List the obvious variants (`-a` cancel, `-b` validation error, `-c` edge).
3. **Reference the UJT IDs from the story's "Done when" field** — this is required, not optional:

```markdown
**Done when:**
[UJT-007] and [UJT-007-a] through [UJT-007-c] pass on the simulator (manual walk or XCUITest), translated and committed in the same PR as the implementation.
```

If you can't write a clear UJT for a story, the story is probably too abstract — that's the forcing function. Split it, sharpen the architecture, or refine the AC before continuing.

Headless stories (backend-only, CLI, data pipeline) don't need UJTs; their "Done when" can describe the verifying test directly. The `ujt-coverage` validator soft-passes when no UJTs exist, so headless projects are unaffected. Mark headless stories with a `**Headless:** yes — verified via {test target}` line so a reader (and Phase 8) knows the UJT omission is deliberate.

## The implementer-side cycle

When a story is picked up for implementation (whether by Claude Code, [[milestone-builder]] / [[ship-issue]], or a human), its UJTs become the executable acceptance contract. The cycle is:

1. **Pre-flight** — read the story's UJTs from `{ProjectName}/User Journey Tests/<Epic>.md`. They define done.
2. **Implement** the production code.
3. **Translate UJTs** to the target runnable form (XCUITest for iOS, Playwright for web, etc.) in the same branch as the production code.
4. **Run** the tests.
5. **Triage failures** — for each failing UJT, decide:
   - **Code wrong** → fix the code.
   - **UJT or AC wrong** → file a design-drift issue, update the UJT/AC to match reality, re-run.
6. Loop 4–5 until all UJTs pass.
7. **Ship** — the PR contains both production code AND the translated tests. Reviewer checks that translated tests align with the UJT prose (drift in one direction is fine if it's documented as a fix-the-design call).

This cycle is exactly what surfaces design-vs-code drift early. If Phase 5 said "tab bar shows five tabs" and the code declares six, the UJT translation fails, gets triaged, and produces either a code fix or a design back-port — not a silent contract violation. See [[milestone-builder]] for how this fits into the per-issue agent flow.

## Pre-Gate Validation

Before completing Phase 5, run:

```bash
python {app-design-skill-path}/scripts/validate.py traceability {project-path}
```

This confirms every MVP `[AC-NNN]` has at least one `[S-NNN]` covering it, and every `[S-NNN]` references valid ACs. PASS (exit 0) required before the gate. A human matrix can miss what regex catches; both checks complement each other.

## Gate
Ask: "Do these stories cover all the MVP acceptance criteria? Are any too big or too small for a single Claude Code session? Anything missing?"
