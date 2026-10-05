# Phase 2: Acceptance Criteria & MVP Scoping

## Purpose
Turn every vision feature into a testable contract, then draw the MVP line. Each criterion defines what the feature should do, what it should not break, and how to prove it works. Each criterion also gets a scope tag so only MVP work flows into downstream phases.

## How to Prompt
> "Let's take the vision and write acceptance criteria for every major feature. For each one, I'll describe: what it should do, what should not break when we add it, and how we prove it works. These criteria are the contract — nothing gets built without approved criteria. We'll also tag each one as MVP, v2, or future so we know what to build first."

## Writing Criteria

For each vision feature `[V-NNN]`, produce one or more acceptance criteria `[AC-NNN]`.

Each criterion has four parts:

1. **It should**: Positive behavior. What the feature does when working correctly. Be specific enough that someone could write a test.
2. **It should not break**: Regression guardrails. What existing functionality must remain intact when this feature is added. Think about adjacent features, performance, data integrity.
3. **How we prove it**: Verification approach. Describe the test scenario(s) — could be automated tests, manual verification steps, or both. Concrete enough that a tester could follow them.

   > [!important] Compute expected values, don't intuit them
   > Any test scenario with a date, time, duration, count, or arithmetic result as the *expected* value must have that value **computed** before being written into prose — use Python, a calculator, or `date`, not intuition. Common offenders: "30 days from {date}", "the badge shows {N+1}", "the user sees {count} items after filtering". Hand-written arithmetic in ACs is a recurring source of Phase 7 Blockers. Pre-computing here avoids the rework loop. Phase 7 re-verifies computed values.

   Tests use the `T-NNN` ID prefix (no brackets — `T-NNN`, not `[T-NNN]`). Each test ID appears exactly once in the canonical AC's "How we prove it" section as its primary definition, and may be referenced from other artifacts. Test IDs are permanent and never reused.
4. **Scope**: One of:
   - `mvp` — Required for the first usable version. Without this, the app doesn't solve its core problem.
   - `v2` — Important but not essential for launch. Clear next step after MVP ships.
   - `future` — Nice to have, speculative, or depends on learning from real usage.

### Scoping Guidance

Help the user draw the MVP line by asking:
- "Can the app be useful without this?"
- "Would you ship to yourself / your first user without this feature?"
- "Does this depend on learning something from real usage first?"

Push back gently if everything is tagged `mvp`. A good MVP is the smallest thing that's actually useful. If the user insists, respect their call — but note the risk.

## Grouping

Create one note per major feature area (not one note per criterion). Group related criteria under their parent feature.

## Sharpen the glossary as you go

Phase 2 is where vague vision-level vocabulary either crystallizes or collapses. As you write criteria, you'll discover terms that are still fuzzy ("the user sees their *records*" — which records? all of them? scoped to what?). Apply [[grill-with-docs]] discipline on the fly:

- Every time a criterion uses a domain noun, check it against `CONTEXT.md`
- If the term is missing, add it
- If the term is overloaded (the user means two different things), split it and update upstream criteria that drift
- If a criterion can't be written without picking between two competing nouns, stop and resolve the term first

Criteria phrased in `CONTEXT.md` vocabulary will pay back tenfold when implementer agents read them in Phase 8 issues. Criteria written in fuzzy ad-hoc vocabulary will produce code that drifts from the design.

The glossary file lives in the vault during Phase 1–2 (greenfield) or in the repo from the start (brownfield) — see SKILL.md "Vault vs. repo split."

## Output: `{ProjectName}/Acceptance Criteria/{FeatureName}.md`

```markdown
---
tags:
  - {project-tag}
  - design
  - acceptance-criteria
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} AC {FeatureName}
---

## Feature: [V-NNN] {Feature Name}

{Brief context from the vision document}

### [AC-001] {Criterion Title} `mvp`

**It should:**
{Specific positive behavior description}

**It should not break:**
{Regression guardrails}

**How we prove it:**
{Verification scenarios}

### [AC-002] {Criterion Title} `v2`

{...same structure}
```

The scope tag (backtick-wrapped `mvp`, `v2`, or `future`) goes in the criterion heading for easy scanning.

## MVP Summary

After all criteria are written and tagged, produce a summary at the end of the phase showing the scope breakdown:

```markdown
## MVP Scope Summary

### MVP ({count} criteria)
- [AC-001] {title}
- [AC-003] {title}
- ...

### v2 ({count} criteria)
- [AC-002] {title}
- ...

### Future ({count} criteria)
- [AC-007] {title}
- ...
```

Include this summary in the last acceptance criteria note or as a callout when presenting the gate.

> [!important] MVP Boundary
> Only `mvp`-tagged criteria flow into Phases 3-8. All criteria are preserved in the acceptance criteria notes for future reference, but architecture, stories, dependencies, and issues are scoped to MVP unless the user explicitly requests otherwise.

## User Journey Test Linking

Each MVP-scoped AC should be paired with at least one User Journey Test (UJT) that proves it via observable behavior in the running app. The AC says *what must be true*; the UJT says *what a user does to demonstrate it*. See [[user-journey-tests.md]] for the DSL, file structure, and execution modes.

When the UJT(s) for an AC are known, add a `proven_by:` line to the AC frontmatter (or the AC heading body) listing the UJT IDs:

```markdown
### [AC-007] Adding a book persists across launches `mvp`
**Proven by:** [UJT-007], [UJT-007-a]
```

This is an opt-in link — it's checked by the `ujt-coverage` validator, not by the core `all` run. Headless ACs (backend, CLI, pipeline) don't need a UJT and can omit the field. UI-bound ACs without a UJT will be surfaced as gaps during Phase 7 review.

## Pre-Gate Validation

Before completing Phase 2, run the validators against the project directory:

```bash
python {app-design-skill-path}/scripts/validate.py traceability {project-path}
python {app-design-skill-path}/scripts/validate.py scope {project-path}
```

`{app-design-skill-path}` is the absolute path to this skill's directory (`<skill-dir>`: wherever the plugin or skill is installed; the validator is `<skill-dir>/scripts/validate.py`). The script can be invoked from any working directory — only the `{project-path}` argument has to be correct.

- `traceability` confirms every AC references a valid `[V-NNN]`.
- `scope` confirms every AC has a `mvp` / `v2` / `future` tag.

Both must return PASS (exit 0). Failures get fixed before the gate.

## Gate

Present all criteria organized by feature, with scope tags visible. Then present the MVP summary. Ask:

"These acceptance criteria are the contract. The MVP set is what we'll architect and build first — v2 and future items are parked for later. Review each one — are the criteria complete and testable, and is the MVP line in the right place?"

If the user has concerns about specific criteria or scope tags, revise and re-present those. Don't require re-approval of unchanged criteria.
