# Diagram patterns for the markdown report

The report goes into the repo as `docs/architecture-review-<date>.md`. Mermaid and ascii both render on GitHub/Gitea. Pick the pattern that fits the candidate; mix them. Don't make every diagram look the same — variety is part of the point.

## Pattern 1: Mermaid graph (the workhorse for call flow / dependencies)

Use when the point is "X calls Y calls Z, and look at the mess." Mermaid `flowchart` or `graph` handles graph shapes reliably.

```markdown
**Before**:

\`\`\`mermaid
flowchart LR
  A[OrderHandler] --> B[OrderValidator]
  B --> C[OrderRepo]
  C -.leak.-> D[PricingClient]
  classDef leak stroke:#dc2626,stroke-width:2px;
  class C,D leak
\`\`\`

**After**:

\`\`\`mermaid
flowchart LR
  A[OrderHandler] --> M[OrderIntake]
  M -.adapter.-> P[PricingPort]
  style M fill:#0f172a,color:#fff
\`\`\`
```

## Pattern 2: Mass diagram (interface-vs-implementation ratio)

Two ascii rectangles per module — one for interface surface, one for implementation. Before: interface rectangle is nearly as tall as the implementation (shallow). After: interface rectangle is short, implementation rectangle is tall (deep).

```
Before — shallow OrderIntake               After — deep OrderIntake

  ┌─────────────┐  interface (large)         ┌──┐       interface (small)
  │             │                            │  │
  │             │                            └──┘
  │             │                            ┌────────────┐
  └─────────────┘                            │            │  implementation
  ┌─────────────┐  implementation (small)    │            │  (absorbs the
  │             │                            │            │   wrappers)
  └─────────────┘                            │            │
                                             │            │
                                             └────────────┘
```

## Pattern 3: Cross-section (layered shallowness)

For "before: 6 thin layers each doing nothing; after: 1 thick band labelled with the consolidated responsibility."

```
Before:                          After:
┌─ HTTP handler ─────────┐       ┌─ OrderIntake ──────────────┐
├─ Validator ────────────┤       │                            │
├─ Mapper ───────────────┤       │  validate · map · persist  │
├─ Repo ─────────────────┤       │  · price · emit            │
├─ Pricing ──────────────┤       │                            │
└─ Event emitter ────────┘       └────────────────────────────┘
```

## Pattern 4: Sequence diagram (when timing or round-trips matter)

```markdown
**Before** — 6 round-trips per Order:

\`\`\`mermaid
sequenceDiagram
  participant H as Handler
  participant V as Validator
  participant R as Repo
  participant P as Pricing
  H->>V: validate(order)
  V->>H: ok
  H->>R: save(order)
  R->>H: id
  H->>P: price(id)
  P->>H: priced
  H->>R: update(priced)
  R->>H: ok
\`\`\`

**After** — 1 round-trip:

\`\`\`mermaid
sequenceDiagram
  participant H as Handler
  participant M as OrderIntake
  H->>M: intake(order)
  M->>H: priced & persisted
\`\`\`
```

## Pattern 5: Call-graph collapse

For visualizing a tree of small modules collapsing into one deep module. Use Mermaid `flowchart` with style overrides showing the "after" tree faded inside one node.

## When to use which

| If the friction is… | Use… |
|---|---|
| Modules calling each other in a confusing chain | Pattern 1 (Mermaid graph) |
| Interface as wide as the implementation | Pattern 2 (mass diagram) |
| N stacked layers each delegating to the next | Pattern 3 (cross-section) |
| Excess round-trips or latency | Pattern 4 (sequence) |
| A tree of small modules that wants to be one big one | Pattern 5 (collapse) |

## Style guidance

- Use `CONTEXT.md` vocabulary for the domain labels in diagrams (call it `OrderIntake`, not `FooBarHandler`).
- Use `LANGUAGE.md` vocabulary for annotations (`seam`, `adapter`, `port`, not `boundary`, `wrapper`, `interface-as-class`).
- Keep diagrams scannable — if a Mermaid diagram has more than ~10 nodes, simplify or split.
- Mark leakage red and the deep module dark in Mermaid (via `classDef` and `style`).
- If a diagram needs a paragraph to be understood, redraw the diagram.
