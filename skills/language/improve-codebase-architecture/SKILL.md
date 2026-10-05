---
name: improve-codebase-architecture
description: "Surface architectural friction in an existing codebase and propose deepening opportunities — refactors that turn shallow modules into deep ones. Walks the code, identifies where modules leak, where interfaces are nearly as complex as the implementation, where tests are hostage to internal structure. Produces a markdown report of candidates ranked by leverage, then drops into a grilling loop on whichever candidate the user picks. Informed by CONTEXT.md (domain vocabulary) and docs/adr/ (decisions not to re-litigate). MANDATORY TRIGGERS: improve architecture, audit architecture, find refactoring opportunities, the codebase is a mess, things are getting tangled, find deep modules, find shallow modules, what should we deepen, architecture review. PROACTIVE TRIGGER: after a milestone merges (between milestones), suggest running this skill before the next milestone starts, so entropy from parallel implementer fan-out doesn't compound."
---

# Improve Codebase Architecture

Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. The aim is testability and AI-navigability. The two are the same goal: a codebase that's easy for an agent to navigate is also easy for tests to exercise through clean interfaces.

## Glossary — use these terms exactly

Consistent language is the whole point. Do not drift into "component," "service," "API," or "boundary." Full definitions in [LANGUAGE.md](references/LANGUAGE.md).

- **Module** — anything with an interface and an implementation (function, class, package, slice)
- **Interface** — everything a caller must know to use the module: types, invariants, error modes, ordering, config. Not just the type signature.
- **Implementation** — the code inside
- **Depth** — leverage at the interface: a lot of behaviour behind a small interface. **Deep** = high leverage. **Shallow** = interface nearly as complex as the implementation.
- **Seam** — where an interface lives; a place behaviour can be altered without editing in place. (Use this, not "boundary.")
- **Adapter** — a concrete thing satisfying an interface at a seam
- **Leverage** — what callers get from depth
- **Locality** — what maintainers get from depth: change, bugs, knowledge concentrated in one place

Key principles (full list in [LANGUAGE.md](references/LANGUAGE.md)):

- **Deletion test** — imagine deleting the module. If complexity vanishes, it was a pass-through. If complexity reappears across N callers, it was earning its keep.
- **The interface is the test surface.**
- **One adapter = hypothetical seam. Two adapters = real seam.**

This skill is *informed* by the project's domain model. **`CONTEXT.md`** gives names to good seams; **`docs/adr/`** records decisions the skill should not re-litigate.

## Process

### 1. Explore

Read **`CONTEXT.md`** and any ADRs in `docs/adr/` first. The glossary tells you what to call things; the ADRs tell you what's already locked in.

Then use the Agent tool with `subagent_type=Explore` to walk the codebase. Don't follow rigid heuristics — explore organically and note where you experience friction:

- Where does understanding one concept require bouncing between many small modules?
- Where are modules **shallow** — interface nearly as complex as the implementation?
- Where have pure functions been extracted just for testability, but the real bugs hide in *how* they're called (no **locality**)?
- Where do tightly-coupled modules leak across their seams?
- Which parts of the codebase are untested, or hard to test through their current interface?

Apply the **deletion test** to anything you suspect is shallow: would deleting it concentrate complexity, or just move it? "Yes, concentrates" is the signal you want.

### 2. Present candidates as a markdown report

Write the report to `docs/architecture-review-<YYYY-MM-DD>.md` in the repo. Keeping it in-repo (vs. a temp HTML file) means the report is versioned, diffable across runs, and accessible to future agent sessions. If the user prefers ephemeral reports, write to `$TMPDIR/architecture-review-<timestamp>.md` instead and tell them the path.

The report is organized as a list of candidate cards followed by a top-recommendation section. For each candidate:

```markdown
## Candidate N: {Title naming the deepening}

**Recommendation strength**: Strong | Worth exploring | Speculative
**Dependency category**: in-process | local-substitutable | ports-and-adapters | mock
**Files involved**:
- `path/to/module-a`
- `path/to/module-b`

### Problem

One or two sentences. Why the current architecture causes friction. Use
CONTEXT.md vocabulary for the domain ("the Order intake module is shallow"),
LANGUAGE.md vocabulary for the architecture ("interface nearly as complex
as the implementation; pricing leaks across the seam").

### Solution

One or two sentences. What changes. Plain English, glossary terms only.

### Before / After

(Mermaid diagram or ascii sketch — see DIAGRAMS.md for patterns)

### Wins

- Leverage: one interface, N call sites
- Locality: bugs concentrate in one module
- Interface shrinks; implementation absorbs the wrappers
- Tests hit one seam instead of three
- Delete 4 shallow wrappers

### ADR considerations

If applicable: contradicts ADR-0007 — but worth reopening because…
```

Mermaid diagrams render natively on GitHub/Gitea and in most markdown viewers. Use them for graph-shaped relationships (call graphs, dependencies); use ascii sketches or pure prose for mass diagrams (interface-vs-implementation ratio) or cross-section diagrams (layered shallowness). See [DIAGRAMS.md](references/DIAGRAMS.md) for patterns.

End the report with a **Top recommendation** section: which candidate you'd tackle first and why.

**Use `CONTEXT.md` vocabulary for the domain and [LANGUAGE.md](references/LANGUAGE.md) vocabulary for the architecture.** If `CONTEXT.md` defines "Order," talk about "the Order intake module" — not "the FooBarHandler" and not "the Order service."

**ADR conflicts**: only surface candidates that contradict an existing ADR when the friction is real enough to warrant revisiting the ADR. Mark them clearly. Do not list every theoretical refactor an ADR forbids.

After writing the file, tell the user the path and ask: "Which of these would you like to explore?" Do NOT propose interfaces yet.

### 3. Grilling loop

Once the user picks a candidate, drop into a grilling conversation. Walk the design tree with them — constraints, dependencies, the shape of the deepened module, what sits behind the seam, what tests survive.

Side effects happen inline as decisions crystallize:

- **Naming a deepened module after a concept not in `CONTEXT.md`?** Add the term to `CONTEXT.md` — same discipline as [[grill-with-docs]]. Create the file lazily if it doesn't exist.
- **Sharpening a fuzzy term during the conversation?** Update `CONTEXT.md` right there.
- **User rejects the candidate with a load-bearing reason?** Offer an ADR, framed as: *"Want me to record this as an ADR so future architecture reviews don't re-suggest it?"* Only offer when the reason would actually be needed by a future explorer to avoid re-suggesting the same thing. See [[language/grill-with-docs/references/ADR-FORMAT.md]].
- **Want to explore alternative interfaces for the deepened module?** See [INTERFACE-DESIGN.md](references/INTERFACE-DESIGN.md) for the parallel-sub-agent pattern.

### 4. Convert to issues

If the user wants to land the deepening, hand off to `/to-issues` with the grilling output as input. The deepening becomes one or more vertical-slice issues, each shippable via `/ship-issue`.

## When to run this skill

- **Between milestones**, before starting the next one. Parallel implementer fan-out degrades architecture silently — running this skill at milestone boundaries surfaces the entropy before it compounds.
- **After every 5–10 PRs** on a feature branch, even mid-milestone.
- **When a bug-fix loop keeps finding root causes that point at "this should be one module instead of three."** The bug pattern is the signal.
- **When the user feels "things are getting messy" but can't name the issue.** The exploration step makes the messiness concrete.

## Composition with other skills

- **Reads**: `CONTEXT.md` for vocabulary; `docs/adr/` for locked-in decisions
- **Writes**: candidates to `docs/architecture-review-<date>.md`; updates `CONTEXT.md` and `docs/adr/` inline during the grilling loop
- **Hands off to**: `/to-issues` for issue decomposition once the user picks a candidate
- **Invokes**: [[grill-with-docs]] discipline during the grilling loop
- **Spawns**: parallel sub-agents via the pattern in [INTERFACE-DESIGN.md](references/INTERFACE-DESIGN.md) when the user wants to explore alternative interfaces

## What NOT to do

- **Do not produce a long generic list of "things that could be better."** The report has to be opinionated about *which* deepenings matter most — strength badges, ranked, top recommendation. A list of 30 weak candidates is useless.
- **Do not re-suggest ADR-rejected ideas without flagging the conflict.** Cheap way to lose user trust.
- **Do not drift from the glossary.** "Component" / "service" / "boundary" creep in unless you're disciplined. The vocabulary is the discipline.
- **Do not propose interfaces in the report.** Save that for the grilling loop on the candidate the user picks. Designing-in-prose for candidates the user doesn't care about is wasted depth.
