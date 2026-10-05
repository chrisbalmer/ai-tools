# Designing alternative interfaces (parallel sub-agent pattern)

When the user wants to explore alternative interfaces for a chosen deepening candidate, use this parallel sub-agent pattern. Based on "Design It Twice" (Ousterhout) — your first idea is unlikely to be the best.

Uses the vocabulary in [LANGUAGE.md](LANGUAGE.md) — **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on and which category they fall into (see [LANGUAGE.md](LANGUAGE.md) — in-process, local-substitutable, ports-and-adapters, mock)
- A rough illustrative code sketch to ground the constraints — not a proposal, just a way to make the constraints concrete

Show this to the user, then immediately proceed to Step 2. The user reads and thinks while the sub-agents work in parallel.

### 2. Spawn sub-agents

Spawn 3+ sub-agents in parallel using the Agent tool (all in a single message so they actually run concurrently). Each must produce a **radically different** interface for the deepened module.

Brief each sub-agent with a separate technical brief (file paths, coupling details, dependency category, what sits behind the seam). The brief is independent of the user-facing problem-space explanation in Step 1. Give each agent a different design constraint:

- **Agent 1**: "Minimise the interface — aim for 1–3 entry points max. Maximise leverage per entry point."
- **Agent 2**: "Maximise flexibility — support many use cases and extension."
- **Agent 3**: "Optimise for the most common caller — make the default case trivial."
- **Agent 4** (if applicable): "Design around ports-and-adapters for cross-seam dependencies."

Include both `LANGUAGE.md` architecture vocabulary and the repo's `CONTEXT.md` domain vocabulary in each brief so all agents name things consistently.

Each sub-agent outputs:

1. **Interface** — types, methods, params, plus invariants, ordering, error modes
2. **Usage example** showing how callers use it
3. **What the implementation hides** behind the seam
4. **Dependency strategy and adapters** (which dependency category, what the adapters are)
5. **Trade-offs** — where leverage is high, where it's thin

### 3. Present and compare

Present designs sequentially so the user can absorb each one, then compare them in prose. Contrast by:

- **Depth** — leverage at the interface
- **Locality** — where change concentrates
- **Seam placement** — internal vs. external seams; one adapter vs. many

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. **Be opinionated** — the user wants a strong read, not a menu.

### 4. Hand off

Once the user picks an interface, hand off to `/to-issues` with the deepening + chosen interface as the input. The deepening becomes one or more vertical-slice issues.

## When to use this pattern

- Use it when the deepening is **load-bearing** (large blast radius, used by many callers) and the interface choice is genuinely contested.
- Skip it when the deepening is obvious — a sub-agent fan-out for a trivial interface is wasted parallelism.
- Skip it when the user is already confident about the interface — confirm before spinning up the fan-out.

## Anti-patterns

- **Three agents producing minor variations of the same interface.** That means the constraints in each brief weren't different enough. Re-brief.
- **Agents producing interfaces that disregard the chosen dependency category.** Re-read [LANGUAGE.md](LANGUAGE.md) — the dependency category determines the testing strategy and constrains the interface shape.
- **No opinionated recommendation at the end.** The whole point is to surface options *and then pick one*. Present the menu, then close the menu.
