---
name: grill-with-docs
description: "Interview the user about a plan, design, or change — challenging it against the project's domain glossary (`CONTEXT.md`) and architectural decisions (`docs/adr/`), updating both inline as decisions crystallise. Sharpens fuzzy terminology, flags conflicts with prior decisions, and produces a shared language between the user and the agent before code is written. MANDATORY TRIGGERS: grill me, grill this, stress-test this plan, challenge this design, sharpen this idea, walk the design tree, build shared language, set up CONTEXT.md, set up ADRs, let's grill before coding. Also use proactively at the start of any non-trivial change to an existing codebase, before dispatching `/ship-issue` or `/to-prd`, so the implementer brief inherits resolved vocabulary."
---

# Grill With Docs

Interview the user relentlessly about every aspect of a plan until you reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing. If a question can be answered by exploring the codebase, explore the codebase instead of asking.

## Why this skill exists

Agents are usually dropped into a project and asked to figure out the jargon as they go. They use twenty words where one will do, and they invent names that drift from the names the user already has in their head. A shared, written glossary fixes this — and the only reliable way to build one is to grill it out of the user *before* code is written.

`CONTEXT.md` is the glossary. `docs/adr/` is the durable record of decisions that should not be re-litigated. Both live **in the repo**, not in the Obsidian vault, because every implementer and reviewer agent needs to read them.

## File layout

Most repos have a single context:

```
/
├── CONTEXT.md
├── docs/
│   └── adr/
│       ├── 0001-event-sourced-orders.md
│       └── 0002-postgres-for-write-model.md
└── src/
```

If a `CONTEXT-MAP.md` exists at the root, the repo has multiple contexts. The map points to where each one lives:

```
/
├── CONTEXT-MAP.md
├── docs/
│   └── adr/                          ← system-wide decisions
├── src/
│   ├── ordering/
│   │   ├── CONTEXT.md
│   │   └── docs/adr/                 ← context-specific decisions
│   └── billing/
│       ├── CONTEXT.md
│       └── docs/adr/
```

Create files lazily — only when you have something to write. If no `CONTEXT.md` exists, create one the moment the first term is resolved. If no `docs/adr/` exists, create it when the first ADR is justified.

## Vault vs. repo split

This skill set uses Obsidian (via [[app-design]]) for *thinking-time* artifacts — vision, acceptance criteria, wireframes, story decomposition, dependency graph, design review. Those live in the vault.

`CONTEXT.md` and `docs/adr/` live **in the repo**, not the vault, because:

- Implementer agents (`/ship-issue`, `/milestone-builder`) read from the repo
- Reviewer agents read from the repo
- The vocabulary in `CONTEXT.md` must match the code's identifiers, and that link is only durable if the glossary travels with the code

During greenfield design (before a repo exists), `CONTEXT.md` is born in the vault under the project directory. The moment the repo is created — typically at Phase 4 of `/app-design` — copy `CONTEXT.md` into the repo root and stop editing the vault copy. ADRs follow the same rule.

## During the session

### Read first

Before grilling, read:

- The repo's `CONTEXT.md` (or `CONTEXT-MAP.md` + each linked file)
- Any ADRs in `docs/adr/` that touch the area being discussed
- The conversation context (the user's plan, the issue body, the parent PRD)

Keep the glossary in mind throughout. Every question you ask is implicitly testing whether the user's words match the glossary.

### Challenge against the glossary

When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"

### Sharpen fuzzy language

When the user uses vague or overloaded terms, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."

### Discuss concrete scenarios

When domain relationships are being discussed, stress-test them with specific scenarios. Invent edge cases and force the user to be precise about the boundaries between concepts.

### Cross-reference with code

When the user states how something works, check whether the code agrees. If you find a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"

### Update CONTEXT.md inline

When a term is resolved, update `CONTEXT.md` right there. Don't batch these up — capture them as they happen. Use the format in [CONTEXT-FORMAT.md](./references/CONTEXT-FORMAT.md).

`CONTEXT.md` is a **glossary and nothing else**. It is not a spec, scratch pad, or repository for implementation decisions. Keep it devoid of implementation details — those belong in ADRs, issue bodies, or code.

### Offer ADRs sparingly

Only offer to create an ADR when all three are true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will wonder "why did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If any of the three is missing, skip the ADR. Use the format in [ADR-FORMAT.md](./references/ADR-FORMAT.md).

## Composition with other skills

- **Inside `/app-design`**: invoke during Phase 1 (Vision) and Phase 2 (Acceptance Criteria) to seed `CONTEXT.md`. Invoke during Phase 4 (Architecture) to lock in ADRs.
- **Inside `/to-prd`**: not invoked automatically — `/to-prd` synthesizes from context that should already be grilled. If the user runs `/to-prd` without a prior grilling session and you notice fuzzy vocabulary, suggest `/grill-with-docs` first.
- **Inside `/triage`**: invoked during issue triage when an incoming issue's description is too thin for an agent brief.
- **Inside `/improve-codebase-architecture`**: invoked during the grilling loop after the user picks a candidate to deepen.

## End-of-session checklist

Before declaring the grilling done:

- [ ] Every fuzzy term the user used has either been resolved in `CONTEXT.md` or explicitly punted
- [ ] No term in the plan conflicts with the existing glossary without being reconciled
- [ ] Decisions that meet the ADR three-test are written as ADRs
- [ ] The user can now state the plan using `CONTEXT.md` vocabulary without effort
