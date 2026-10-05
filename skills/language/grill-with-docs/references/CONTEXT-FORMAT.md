# CONTEXT.md Format

`CONTEXT.md` is a project-specific glossary. It defines the terms your codebase uses for domain concepts, and the terms it deliberately avoids. It lives at the repo root (or under a sub-context directory if the repo uses `CONTEXT-MAP.md`).

## Structure

```md
# {Context Name}

{One or two sentence description of what this context is and why it exists.}

## Language

**Order**:
A confirmed customer purchase that has entered the fulfillment pipeline. An Order
exists from confirmation onward; cart contents before confirmation are not Orders.
_Avoid_: Purchase, transaction

**Invoice**:
A request for payment sent to a Customer after delivery of an Order.
_Avoid_: Bill, payment request

**Customer**:
A person or organization that places Orders.
_Avoid_: Client, buyer, account

## Relationships

- A **Customer** places many **Orders**
- An **Order** generates exactly one **Invoice** after fulfillment

## Flagged ambiguities

- "Account" was previously used to mean both **Customer** and **User** — resolved:
  **Customer** is the billable entity; **User** is the login identity. They may
  refer to the same person but they are not interchangeable.

## Example dialogue

> Dev: "When the Customer cancels the Order before fulfillment, does the Invoice
> get voided?"
>
> Domain expert: "There's no Invoice yet — Invoices only exist post-fulfillment.
> The Order moves to `cancelled` and the cart is discarded."
```

## Rules

- **Be opinionated.** When multiple words exist for the same concept, pick the best one and list the others as aliases to avoid.
- **Flag conflicts explicitly.** If a term is used ambiguously in the codebase, call it out under "Flagged ambiguities" with a clear resolution.
- **Keep definitions tight.** One or two sentences max. Define what the term IS, not what it does.
- **Show relationships.** Bold term names so they read as a connected graph. Express cardinality (one, many) where obvious.
- **Only include terms specific to this project's context.** General programming concepts (timeouts, error types, utility patterns) don't belong here, even if the project uses them extensively. Before adding a term, ask: is this concept unique to this context, or general programming? Only the former belongs.
- **Group terms under subheadings** when natural clusters emerge. If all terms belong to a single cohesive area, a flat list is fine.
- **Write an example dialogue.** A conversation between a dev and a domain expert that demonstrates how the terms interact naturally and clarifies boundaries between related concepts.

## What does NOT belong in CONTEXT.md

- Implementation details (which database, which framework, file paths, function signatures)
- Architectural decisions — those go in `docs/adr/`
- Roadmap items, TODOs, deferred work
- Code snippets beyond very small illustrative ones in the example dialogue
- API contracts, schema definitions, type shapes — those live in the code itself

If you find yourself writing any of the above into `CONTEXT.md`, stop. It belongs somewhere else.

## Single vs. multi-context repos

**Single context (most repos):** One `CONTEXT.md` at the repo root.

**Multiple contexts (large or bounded-context repos):** A `CONTEXT-MAP.md` at the repo root lists the contexts, where they live, and how they relate. Each context gets its own `CONTEXT.md`:

```md
# Context Map

## Contexts

- [Ordering](./src/ordering/CONTEXT.md) — receives and tracks customer orders
- [Billing](./src/billing/CONTEXT.md) — generates invoices and processes payments
- [Fulfillment](./src/fulfillment/CONTEXT.md) — manages warehouse picking and shipping

## Relationships

- **Ordering → Fulfillment**: Ordering emits `OrderPlaced` events; Fulfillment consumes them to start picking
- **Fulfillment → Billing**: Fulfillment emits `ShipmentDispatched` events; Billing consumes them to generate invoices
- **Ordering ↔ Billing**: Shared types for `CustomerId` and `Money`
```

Infer the structure:

- If `CONTEXT-MAP.md` exists, read it to find contexts
- If only a root `CONTEXT.md` exists, single context
- If neither exists, create a root `CONTEXT.md` lazily when the first term is resolved

When multiple contexts exist, infer which one the current topic relates to. If unclear, ask.

## When to split a single CONTEXT.md into a CONTEXT-MAP.md

Two signals:

1. **Vocabulary collisions are appearing.** The same word means different things in different parts of the app — "Order" in the customer-facing area vs. "Order" as a fulfillment slot — and you keep having to disambiguate inline.
2. **The glossary is approaching 40+ terms.** A flat glossary that large stops being scannable.

When you hit either signal, propose the split to the user and create `CONTEXT-MAP.md` once they approve.

## When to update CONTEXT.md

- Inside `/grill-with-docs` whenever a term is resolved.
- Inside `/app-design` Phase 1–2 as vocabulary emerges from vision and acceptance criteria.
- Inside `/ship-issue` and `/milestone-builder` implementer briefs when a PR introduces a domain term. The implementer adds the term as part of the same PR.
- Inside `/improve-codebase-architecture` when a deepened module gets named after a concept that wasn't already in the glossary.

Never let a domain term land in code without being in `CONTEXT.md`. Reviewers must flag any drift.
