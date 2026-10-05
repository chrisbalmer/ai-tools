# Phase 7: Design Review

## Purpose
Full walkthrough of everything produced in Phases 1-6. This is the final gate before creating implementation issues. Verify coverage, consistency, completeness, and identify risks.

## Reviewer Selection

> [!important] Always spawn a fresh session for Phase 7 review
> The author session is biased toward confirming its own work. It tends to skim what it just wrote, miss its own arithmetic mistakes, and treat its own decisions as already-justified. **Phase 7 is run by a fresh session that did not author Phases 5 or 6** — ideally one that has not seen the design conversation at all and reads only the artifacts.

The same rule applies to **re-reviews of rework**: each rework iteration gets a *fresh* verifier, not the session that performed the rework. Re-review by the rework author is not verification — it's confirmation bias with extra steps.

In practice: spawn a subagent (or new session) for Phase 7 and for every subsequent verification pass. Hand it the project path and the rework summary; let it work from artifacts.

## When the First Review Finds Blockers

A clean PASS on the first pass is uncommon for non-trivial designs. The expected pattern is multi-pass:

1. **Pass 1** (fresh reviewer): finds Blockers, Concerns, Nits. Writes a review report.
2. **Rework** (author session, or a different session — but *not* the reviewer): addresses each Blocker. Documents what changed.
3. **Pass 2** (a *different* fresh reviewer — not the Pass 1 reviewer, not the rework author): re-verifies Blockers are resolved and checks for regressions.
4. Repeat with fresh verifiers until verdict is **PASS with zero Blockers**.

This converges. A real v2.0 design cycle needed five passes to land. Treat each pass as a normal step, not a failure. The point is the convergent trajectory, not pass-1 perfection.

After every rework, run `python {app-design-skill-path}/scripts/validate.py all {project-path}` before declaring the rework done. Validator failures are automatic Blockers — they don't need a human to flag them. (See "Pre-Review Validation" below.)

## Pre-Review Validation

> [!important] Run validators first; failures are automatic Blockers
> Before any of the manual checklist below, run:
> ```bash
> python {app-design-skill-path}/scripts/validate.py all {project-path}
> ```
> This runs `traceability`, `ids`, `orphans`, `scope`, and `migrations` in one shot. Any non-zero exit is an automatic Blocker and goes into the review report without further analysis. Fix and re-run before continuing the human review.

## Review Checklist

Work through each of these systematically and present findings. The first item is the validator; everything after is human judgment that regex can't do.

### 0. Validators

Run `python {app-design-skill-path}/scripts/validate.py all {project-path}`. Capture the output. PASS required to continue; any failure is a Blocker.

### 1. Traceability Coverage

Build the full chain and verify completeness:

| Vision Feature | Acceptance Criteria (MVP) | Screens | Stories |
|---|---|---|---|
| [V-001] {name} | [AC-001], [AC-002] | [SCR-001] | [S-001], [S-002], [S-003] |

Check for:
- Every `[V-NNN]` with MVP criteria has stories
- Every `mvp` `[AC-NNN]` has at least one `[S-NNN]`
- Every `[SCR-NNN]` has stories that build it
- No orphan stories (stories that don't trace back to an AC)

### 2. Architecture ↔ Story Consistency

- Are there stories that assume a component, API, or data entity not described in the architecture doc?
- Are there architecture components that no story builds?
- Do stories reference the correct files/modules based on the component map?
- For brownfield: do any stories conflict with documented existing conventions?

### 3. Cross-Cutting Concerns Verification

Revisit every item from the Architecture phase's cross-cutting concerns checklist. For each one that was addressed (not deferred), verify that stories exist to implement it:

| Concern | Architecture Decision | Implementing Stories |
|---------|----------------------|---------------------|
| Error handling | {approach} | [S-NNN], [S-NNN] |
| Loading & empty states | {approach} | [S-NNN] |
| Offline behavior | Deferred | — |
| Logging & observability | {approach} | [S-NNN] |
| Data migration | {approach} | [S-NNN] |
| First-run experience | {approach} | [S-NNN] |
| Backup & recovery | Deferred | — |
| Configuration | {approach} | [S-NNN] |
| Testing strategy | {approach} | Embedded in each story |
| CI/CD | {approach} | [S-NNN] |

Flag any concern that was addressed in architecture but has no implementing story — that's a gap.

### 4. Completeness — Implicit Requirements

Look for things commonly missed. Check if stories exist for:
- Initial project scaffolding (repo setup, dependency installation, base config)
- Database schema creation / migration tooling setup
- Auth flow (login, logout, session handling, token refresh)
- Form validation (client-side and server-side)
- Pagination for list views
- Search/filter if any screen has more than ~20 items
- Notification or feedback for async operations
- 404 / not found handling
- Permission checks beyond "is the user logged in"

Not all of these are needed for every project — but each should be consciously included or excluded.

### 5. Sizing Review

Review story sizes against Claude Code sizing guidance:
- Flag any story touching 4+ files
- Flag any story mixing frontend and backend
- Flag any story with vague "done when" criteria
- Flag any story that requires architectural decisions not captured in Phase 4

### 6. Dependency Review

- Are there circular dependencies in the build order?
- Can any stories be moved to an earlier phase to unblock more work?
- Is the critical path reasonable, or is there a bottleneck that could be broken up?

### 7. Computed Expected Values

Hand-written arithmetic in ACs is a recurring Blocker source. For every test scenario in `Acceptance Criteria/` that asserts a date, time, duration, count, or arithmetic result, **re-compute the expected value** (Python, calculator, `date`) and confirm it matches what the AC says.

Common offenders:
- "X days from {anchor date}" — recompute with `date -d` or `datetime.timedelta`
- "the badge shows {N+1}" — recompute against the seed data
- "the user sees {count} items after filtering" — recompute against the documented filter rules

A mismatch is a Blocker. The fix is in the AC prose, not the verification — the test is right, the AC was wrong.

### 8. Code-vs-Design Re-sync

When code already exists (brownfield projects, or promotion-cycle v2+ bundles where MVP shipped), the design documents make claims about the codebase that may be stale. Verify them before approving:

- **Migration count / numbering**: design says "the next migration will be 0042" — is the current head actually 0041?
- **Entity existence**: design references a table or model — does it exist in the schema?
- **Framework / library versions**: design assumes a feature available only in version X — is the installed version ≥ X?
- **API patterns**: design says "follows the existing REST convention" — does that convention actually exist in the code, and as described?
- **File / module paths**: design references files — do they exist at those paths?

For each design claim about the codebase, spot-check it. Surface stale claims as Blockers; the design must match reality before issues are created.

This step is *required* for brownfield and for any promotion-cycle pass on a project where code has been written. It is *optional* for pure greenfield where no code exists yet.

### 9. Did the Rework Propagate?

On any pass after Pass 1, before signing off, verify the rework propagated to every artifact that mentions the concept being reworked:

- The rework should have produced a pre-edit audit (see `promotion-cycle.md`) listing every artifact touching the concept.
- Walk the list: each artifact reflects the rework, none still references the old name / shape / behavior.
- Missed propagation is one of the most common multi-pass Blockers.

If the pre-edit audit is missing, ask for one before approving.

### 10. User Journey Test Coverage

For UI-bearing projects, verify the journey-form proof exists alongside the AC-form contract:

- Every story has at least one UJT in `{ProjectName}/User Journey Tests/`.
- Every MVP `[AC-NNN]` is referenced by at least one UJT's `traces_to:` (or otherwise has a documented headless verification path).
- Variants exist for the obvious edges: cancel mid-flow, validation errors, duplicate / empty / max inputs.
- The story "Done when" lines name the UJT IDs that must pass.

Run `python {app-design-skill-path}/scripts/validate.py ujt-coverage {project-path}` to surface uncovered MVP ACs automatically. Note that `ujt-coverage` is *not* part of `validate.py all` — it's opt-in for UI-heavy projects. For headless projects (backend, CLI, pipelines), skip this step entirely; the AC's "How we prove it" section is sufficient.

See [[user-journey-tests.md]] for the DSL and authoring conventions.

### 11. Comp Coverage

For UI-bearing projects, verify every `[SCR-NNN]` in the wireframe inventory has corresponding Comp files in the Design bundle (`design_handoff_<project>/`). Check that a screenshot PNG and prototype source file exist for each screen.

A screen without a Comp is a Blocker — the Design bundle is incomplete, and downstream stages (implementer Comp matching, reviewer Visual diff gate, e2e Comp diff pass) will have no visual source of truth for that screen.

For backend-only or headless projects, skip this step (no screens = no Comps).

### 12. Risk Register

Identify the highest-risk stories and areas:
- New technology the team/user hasn't used before
- Complex external integrations
- Unclear or ambiguous requirements
- Performance-sensitive paths
- Data integrity critical paths

For each risk, suggest a mitigation: spike story, fallback plan, or explicit acceptance of the risk.

## Output: `{ProjectName}/Design Review.md`

For multi-pass cycles, append each pass to the same file rather than overwriting — the trajectory matters. Use `Design Review - v2.md` etc. for promotion-cycle passes.

```markdown
---
tags:
  - {project-tag}
  - design
  - review
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} Design Review
---

## Pass {N} — {YYYY-MM-DD}

**Reviewer:** {fresh session id / "fresh subagent"}
**Verdict:** {PASS | PASS-with-Concerns | FAIL}
**Blockers:** {count}
**Concerns:** {count}
**Nits:** {count}

**Validator output:** {paste `validate.py all` result, or "PASS"}

## Traceability Matrix

| Vision Feature | Acceptance Criteria (MVP) | Screens | Stories |
|---|---|---|---|
| [V-001] {name} | [AC-001], [AC-002] | [SCR-001] | [S-001], [S-002], [S-003] |
| ... | ... | ... | ... |

## Coverage Gaps
{Any gaps found, or "None — all MVP features traced through to stories."}

## Architecture ↔ Story Consistency
{Any conflicts found, or "No inconsistencies found."}

## Cross-Cutting Concerns Status

| Concern | Status | Stories |
|---------|--------|---------|
| Error handling | Covered | [S-NNN] |
| Loading & empty states | Covered | [S-NNN] |
| Offline behavior | Deferred to v2 | — |
| Logging & observability | Covered | [S-NNN] |
| Data migration | Covered | [S-NNN] |
| First-run experience | Covered | [S-NNN] |
| Backup & recovery | Deferred | — |
| Configuration | Covered | [S-NNN] |
| Testing strategy | Embedded | per-story |
| CI/CD | Covered | [S-NNN] |

## Completeness Additions
{Implicit requirements discovered. For each, note whether it needs a new AC + story or just a note on an existing story.}

## Sizing Concerns
{Stories that should be split, with suggestions. Or "All stories within Claude Code sizing guidelines."}

## Dependency Issues
{Circular deps, optimization opportunities. Or "No issues found."}

## Code-vs-Design Re-sync
{Spot-check results for design claims about the codebase — migration counts, entity existence, framework versions, file paths. Or "Greenfield — no code to re-sync against." Or "All claims verified." See checklist item 8.}

## Rework Propagation (Pass 2+)
{For passes after Pass 1: confirmation that the pre-edit audit exists and every artifact in it reflects the rework. Or "Pass 1 — not applicable." See checklist item 9.}

## User Journey Test Coverage
{`ujt-coverage` validator output, uncovered MVP ACs, missing variants. Or "Headless project — UJTs not required." See checklist item 10.}

## Comp Coverage
{For UI projects: list every [SCR-NNN] and whether a screenshot + prototype file exists in the Design bundle. Flag any screen without a Comp as a Blocker. Or "Backend-only — no Comps required." See checklist item 11.}

## Risk Register

| Risk | Impact | Likelihood | Mitigation |
|------|--------|-----------|------------|
| {description} | {what goes wrong} | {high/med/low} | {what to do} |

## Final Recommendation
{Summary: ready to proceed to issue creation, or what needs to change first}
```

## Gate

This is the big one. Ask: "This is the final design review before we create implementation issues. Review the findings above. Are you satisfied with the design, or do we need to revise any phases?"

If the review found Blockers, **do not present this as the final gate.** Present the review report, then start the rework loop: author addresses Blockers, a fresh verifier re-reviews, repeat until verdict is PASS with zero Blockers. Only then ask the user the final gate question. The user sees the final state, with the multi-pass trajectory captured in `Design Review.md` for the record.
