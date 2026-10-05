---
name: to-prd
description: "Lightweight PRD path for brownfield features — synthesize the current conversation context into a PRD and publish it as an issue on the project's Gitea tracker. No interview; assumes the user has already grilled the idea (manually or via /grill-with-docs). Produces a single issue body covering problem, solution, user stories, implementation decisions, testing decisions, and out-of-scope. The right tool when the change is feature-shaped on an existing app and does not warrant the full 8-phase /app-design funnel. MANDATORY TRIGGERS: write a PRD, draft a PRD, turn this into a PRD, ship this as an issue with context, file this as a feature request, capture this as a PRD, write up the spec. Do NOT use for greenfield apps (use /app-design instead) or for breaking a PRD into buildable issues (use /to-issues after this one)."
---

# To PRD

Take the current conversation context and the user's codebase understanding and produce a PRD. **Do not interview the user** — synthesize what you already know. If you find yourself with major unresolved questions, the conversation hasn't been grilled enough; stop and suggest `/grill-with-docs` first.

The output is published as a single Gitea issue with the `ready-for-agent` triage label (or your repo's equivalent). The PRD becomes the parent issue; `/to-issues` then breaks it into independently-grabbable sub-issues.

## When to use this vs. /app-design

- **`/to-prd`** — feature-shaped addition to an existing app. Single PRD, one parent issue, decomposed into tracer-bullet sub-issues. Lightweight.
- **`/app-design`** — greenfield app, or major brownfield expansion that needs vision + acceptance criteria + wireframes + architecture work before it can be sliced. Heavy.

If you're unsure, ask yourself: would the full 8-phase funnel produce meaningful output for this change, or would Phases 1–3 be ceremony? If it's the latter, use `/to-prd`.

## Process

### 1. Explore the repo if you haven't already

Read enough of the codebase to write the PRD in the project's vocabulary. **Specifically read:**

- `CONTEXT.md` — the domain glossary. Use these terms exactly in the PRD; the implementer brief will too. Drift here propagates everywhere.
- Any `docs/adr/*.md` that touches the area you'll be changing. The PRD must not propose decisions an ADR has already settled (or it must explicitly call out that it's revisiting one, with reasoning).
- The 1–3 files that anchor the idiomatic pattern for this kind of change.

If `CONTEXT.md` does not exist in the repo, stop. Run `/grill-with-docs` first to seed it — a PRD written without a glossary will be written in fuzzy ad-hoc vocabulary, and the implementer will introduce code identifiers that don't match the design.

### 2. Sketch out the major modules

Sketch the major modules you would build or modify to land this feature. **Actively look for opportunities to extract deep modules** that can be tested in isolation.

A **deep module** (vs. a shallow one) encapsulates a lot of functionality behind a simple, testable interface that rarely changes. See [[language/improve-codebase-architecture/references/LANGUAGE.md]] for the vocabulary.

Check with the user that these modules match their expectations and which ones they want tests written for. This is the only checkpoint in `/to-prd` — past this point you're synthesizing, not interviewing.

### 3. Write the PRD and publish it

Use the template below. Publish to Gitea via `mcp__gitea__issue_write` (create method). Apply the `ready-for-agent` label (or your repo's equivalent — check `MEMORY.md`). The parent PRD does not need additional triage.

```markdown
## Problem Statement

The problem the user is facing, from the user's perspective. One or two paragraphs.

## Solution

The solution to the problem, from the user's perspective. What changes for them.
One or two paragraphs.

## User Stories

A numbered list, one line per story:

1. As an <actor>, I want a <feature>, so that <benefit>

Cover all aspects of the feature, including edge cases and admin/maintenance
flows — `/to-issues` will draw vertical slices from these and you don't want
gaps. Completeness comes from more stories, not longer ones: one sentence per
story, nothing after the <benefit> clause.

## Implementation Decisions

A list of implementation decisions made — one bullet per decision, one or two
sentences each. State the decision, not the deliberation. Include:

- Modules to build/modify (use CONTEXT.md vocabulary in module names)
- Interfaces being added or changed (shape, not file paths)
- Technical clarifications from the developer
- Architectural decisions — if any of these meet the ADR three-test
  (hard to reverse / surprising / real trade-off), the implementer drops
  an ADR in `docs/adr/` as part of the first PR that lands the decision
- Schema changes (entities affected, what the new state looks like)
- API contracts (request/response shape, error modes)
- Specific interactions between modules

Do NOT include specific file paths or code snippets — they go stale quickly.

Exception: if a prototype produced a snippet that encodes a decision more
precisely than prose (state machine, reducer, schema, type shape), inline
it in the relevant decision and note that it came from a prototype. Trim
to the decision-rich parts — not a working demo.

## Testing Decisions

A list of testing decisions — same discipline, one or two sentences per bullet:

- What makes a good test on this codebase (only test external behavior,
  not implementation details)
- Which modules will get tests, and at what seam
- Prior art for these tests (similar test types already in the repo)
- Use TDD discipline (red-green-refactor, vertical slices) — see /tdd

## Out of Scope

Things explicitly excluded from this PRD. Clear "no"s prevent
gold-plating during implementation.

## Further Notes

Any context that doesn't fit elsewhere. Cross-references to related issues,
relevant past discussions, deferred decisions.
```

### 4. Hand off to /to-issues

After the PRD lands, suggest the user run `/to-issues <PRD issue number>` to break it into vertical slices. Don't auto-spawn — the user picks the granularity.

## Composition with other skills

- **Before**: `/grill-with-docs` if the conversation has fuzzy vocabulary. Skip if the user has already done the grilling.
- **After**: `/to-issues` to decompose the PRD into independently-grabbable issues.
- **For each issue**: `/ship-issue` (or `/milestone-builder` if grouped into a milestone).

## What NOT to do

- **Do not interview the user.** If you have unresolved questions, stop and suggest `/grill-with-docs`. `/to-prd` is for synthesis, not discovery.
- **Do not include file paths or code snippets in the PRD body.** Both go stale fast and the implementer should be free to choose the right place.
- **Do not make architectural decisions that should be ADRs without flagging them.** The PRD can name a decision (e.g., "use event sourcing for the audit log"); the implementer drops the ADR when they land the first commit that depends on it.
- **Do not skip the `CONTEXT.md` read.** Writing a PRD in ad-hoc vocabulary is the source of "we shipped the feature but the names are wrong everywhere" — the failure mode this whole skill set exists to prevent.
