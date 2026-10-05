# ADR Format

ADRs (Architecture Decision Records) live in `docs/adr/` and use sequential numbering: `0001-slug.md`, `0002-slug.md`, etc. They record decisions that are **hard to reverse**, **surprising without context**, and the **result of a real trade-off** — decisions a future reader (human or agent) will need the reasoning behind to avoid relitigating.

Create the `docs/adr/` directory lazily — only when the first ADR is needed.

## Template

```md
# {Short title of the decision}

{1–3 sentences: what's the context, what did we decide, and why.}
```

That's it. An ADR can be a single paragraph. The value is in recording *that* a decision was made and *why* — not in filling out sections for their own sake.

## Optional sections

Only include these when they add genuine value. Most ADRs will not need them.

- **Status** frontmatter (`proposed | accepted | deprecated | superseded by ADR-NNNN`) — useful when decisions are revisited
- **Considered Options** — only when the rejected alternatives are worth remembering
- **Consequences** — only when non-obvious downstream effects need to be called out

## Numbering

Scan `docs/adr/` for the highest existing number and increment by one. IDs are permanent — never renumber or reuse, even when an ADR is deprecated.

## When to offer an ADR

All three must be true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If a decision is easy to reverse, skip it — you'll just reverse it. If it's not surprising, nobody will wonder why. If there was no real alternative, there's nothing to record beyond "we did the obvious thing."

### What qualifies

- **Architectural shape.** "We're using a monorepo." "The write model is event-sourced; the read model is projected into Postgres."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target. Not every library — just the ones that would take a quarter to swap out.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; other contexts reference it by ID only." The explicit no-s are as valuable as the yes-s.
- **Deliberate deviations from the obvious path.** "We're using manual SQL instead of an ORM because X." Anything where a reasonable reader would assume the opposite. These stop the next engineer from "fixing" something that was deliberate.
- **Constraints not visible in the code.** "We can't use AWS because of compliance requirements." "Response times must be under 200ms because of the partner API contract."
- **Rejected alternatives when the rejection is non-obvious.** If you considered GraphQL and picked REST for subtle reasons, record it — otherwise someone will suggest GraphQL again in six months.

### What does NOT belong in an ADR

- Coding style preferences (those go in `CLAUDE.md` or the repo's lint config)
- Domain vocabulary (that goes in `CONTEXT.md`)
- TODOs, deferred decisions, "we'll figure this out later"
- Decisions a reasonable reader would default to anyway
- Discussions that did not lead to a decision

## Example ADRs

### Example 1: tight

```md
# 0003 — Postgres for the write model, projected to ClickHouse for analytics

The write model needs strong ACID guarantees because Orders cannot be lost or double-applied;
the read model needs fast aggregations across millions of historical rows. Postgres + CDC into
ClickHouse gives us both without forcing one store to be bad at the other workload.
```

### Example 2: with rejected alternatives

```md
# 0007 — Synchronous REST between Ordering and Billing

We considered domain events but Billing must reflect Order state in under 200ms for the
partner-API SLA. Event consumption with replay would not meet that latency budget reliably.
We accept the coupling and revisit if we can renegotiate the SLA.

Considered: NATS events with eventual consistency. Rejected because the SLA is hard-bound.
```

## Composition with other skills

- `/grill-with-docs` is the primary author of ADRs. The grilling session surfaces real trade-offs and offers an ADR at the right moment.
- `/app-design` Phase 4 (Architecture) emits initial ADRs as architectural decisions are locked in.
- `/improve-codebase-architecture` offers an ADR when the user rejects a deepening candidate for a load-bearing reason — to stop future review runs from re-suggesting it.

## Updating or deprecating an ADR

- If a decision changes, add a new ADR that supersedes the old one. Set the old ADR's status to `superseded by ADR-NNNN`. Do not delete or rewrite the old ADR — the history of the reasoning matters.
- If a decision was wrong, add a new ADR explaining what changed and why. The old ADR is part of the institutional memory.
