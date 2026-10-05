---
name: to-issues
description: "Break a PRD, plan, or spec into independently-grabbable Gitea issues using tracer-bullet vertical slices — each slice cuts through every layer (schema → API → UI → tests) end-to-end, not horizontally per layer. Quizzes the user on the proposed slicing, iterates, then publishes each slice as a Gitea issue with dependency links between them. The natural follow-up to /to-prd; also runs after /app-design Phase 8 if you want a lighter slicing pass. MANDATORY TRIGGERS: break this into issues, slice this PRD, decompose this plan, turn the PRD into tickets, vertical slice this, tracer bullet issues, draft sub-issues, file these as separate issues, split this work."
---

# To Issues

Break a plan, spec, or PRD into independently-grabbable issues using **vertical slices** (tracer bullets). Each issue is a thin slice that cuts through every integration layer end-to-end, not a horizontal slice of one layer.

## Why vertical, not horizontal

A horizontal slice ("build the schema for everything, then build the API, then build the UI") feels orderly but produces nothing demoable until the last layer lands. A vertical slice ("build the schema + API + UI for *one user story*") is demoable the moment it merges, even if many other user stories are still on the backlog.

For agent-driven implementation, vertical slices have a second advantage: each issue can be implemented in isolation by a single Implementer agent without the integration-test gap that horizontal slices create.

## Process

### 1. Gather context

Work from whatever is in the conversation context. If the user passes an issue reference (issue number, URL, or filename) as an argument, fetch it from Gitea via `mcp__gitea__issue_read` and read its full body and comments.

### 2. Explore the codebase if you haven't already

Read enough to write issue titles and descriptions in the project's vocabulary. **Read `CONTEXT.md` and any ADRs in `docs/adr/` that touch the area** — issue bodies must use the glossary's terms; the implementer brief inherits that discipline.

If `CONTEXT.md` does not exist, stop and suggest `/grill-with-docs` first. Issues without shared vocabulary become a source of drift.

### 3. Draft vertical slices

Break the plan into tracer-bullet issues. Each slice has a type:

- **AFK** — can be implemented and merged by an agent without human interaction. Prefer these.
- **HITL** (human-in-the-loop) — requires human judgment (architectural decision, design review, manual UI test the agent can't run). Use sparingly.

Vertical-slice rules:

- Each slice delivers a narrow but **complete** path through every relevant layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones — thin slices give the agent loop more checkpoints and produce a tighter feedback cadence

**Foundation slice (slice 0):** For UI projects, the first slice must be a Foundation slice that extracts the Comp's visual language into code — design tokens, shared layout components, base styles. It blocks every UI-touching slice and is blocked by nothing. Without it, parallel Implementers independently invent colors and spacing. List the Design bundle directory path in the Foundation slice's **Technical Notes** as extraction source material. Its `## Comp Reference` should read `Foundation — no screen rendering; Comps consumed as extraction source` (the Visual diff gate does not fire on this sentinel text).

**Comp-backed AC:** Every slice that touches a screen must include an AC: `Rendered output matches Comp for [SCR-NNN]` (reference the Comp screenshot path in the Design bundle). This is what the Visual diff gate checks during review.

### 4. Quiz the user on the slicing

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title** — short, descriptive, uses `CONTEXT.md` vocabulary
- **Type** — AFK / HITL
- **Blocked by** — which other slices (if any) must complete first
- **User stories covered** — which user stories from the source PRD this addresses

Ask the user:

- Does the granularity feel right? Too coarse / too fine?
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the right slices marked HITL vs. AFK?

Iterate until the user approves the breakdown. **Do not publish before approval** — re-slicing after publication is more painful than getting it right the first time.

### 5. Publish the issues to Gitea

Publish each approved slice via `mcp__gitea__issue_write` (create method). Use the issue body template below. Apply the `ready-for-agent` label (or your repo's equivalent — check `MEMORY.md`).

**Publish in dependency order** (blockers first) so you can reference real Gitea issue numbers in the "Blocked by" field. For each issue after creation, capture the returned issue number for use in subsequent issues' `Blocked by` lines.

```markdown
## Parent

References #<PRD issue number> (omit this section if the source wasn't an existing issue)

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior,
not layer-by-layer implementation steps. Use CONTEXT.md vocabulary.

Avoid file paths or code snippets — they go stale fast.

Exception: if a prototype produced a snippet that encodes a decision more
precisely than prose (state machine, reducer, schema, type shape), inline it
here and note that it came from a prototype. Trim to the decision-rich parts.

## Acceptance criteria

- [ ] Concrete, testable criterion 1
- [ ] Concrete, testable criterion 2
- [ ] Concrete, testable criterion 3
- [ ] Rendered output matches Comp for [SCR-NNN] (if this slice touches UI — path: `design_handoff_<project>/screenshots/NN-<name>.png`)

## Comp Reference

{Reference the Comp files in the Design bundle for each [SCR-NNN] this slice renders.
Omit this section for backend-only slices.}

## Dependencies

**Blocked by:** #N, #M  (or "None — can start immediately")
**Blocks:** #X, #Y      (filled in retroactively as later slices reference this one)
```

The `Dependencies` block uses the format `/milestone-builder` parses. If you want this batch of issues to ship as a coordinated milestone, also attach them to a Gitea milestone via `mcp__gitea__milestone_write` and `mcp__gitea__issue_write` (update method).

### 6. Hand off

Tell the user what was created. Suggest:

- `/ship-issue <N>` for any single AFK slice they want to land immediately
- `/milestone-builder` if the slices were attached to a milestone and they want to fan out

Do NOT close or modify the parent PRD issue — it stays open as the umbrella reference until all sub-issues merge.

## Composition with other skills

- **Before**: `/to-prd` (lightweight) or `/app-design` Phase 8 (heavy). Either produces a plan; `/to-issues` slices it.
- **After**: `/ship-issue` per slice, or `/milestone-builder` if grouped into a milestone.

## What NOT to do

- **Do not publish before user approval.** The slicing is the value-add of this skill; publishing too early destroys the iteration loop.
- **Do not draw horizontal slices.** "Schema PR / API PR / UI PR" produces issues that can't be implemented independently and gives the agent loop nothing demoable until the last one merges.
- **Do not introduce vocabulary not in `CONTEXT.md`.** If a slice needs a term that's missing, add it to `CONTEXT.md` first (or surface to the user that the glossary is incomplete).
- **Do not over-slice.** A slice that can't deliver any user-observable behavior on its own (e.g., "add a private helper function") is too thin. Combine with the slice that uses it.
