# Phase 4: Architecture & Technical Design

## Purpose
Define how the system holds together. Data model, API boundaries, component map, technology decisions. Answer "how does this thing work?" without writing implementation code. Only architect what's needed for `mvp`-tagged acceptance criteria.

## Move CONTEXT.md and ADRs into the repo

If this is a greenfield project, the repo is created during or just before Phase 4 (you're committing to a tech stack and need somewhere to put a scaffold). The moment the repo exists:

1. **Copy `{ProjectName}/CONTEXT.md` (vault) → `<repo>/CONTEXT.md`**. From now on, the repo copy is canonical. Do not edit the vault copy — instead, delete it, or replace its contents with a one-line pointer: `Moved to <repo path>/CONTEXT.md`.
2. **Create `<repo>/docs/adr/`** if any ADRs are about to land.
3. **Update Phase 4 references to ADRs** — the `[D-NNN]` IDs used in this skill's design artifacts map onto `docs/adr/0NNN-<slug>.md` files in the repo. Both records exist: the vault keeps the design-time list for traceability; the repo holds the durable ADR.

For brownfield projects, the repo already exists with `CONTEXT.md` and `docs/adr/` (or you create them on first need). Read them before designing changes.

See [[grill-with-docs]] for the format of both files.

## Brownfield: Start with Current State

If this is a brownfield project, begin by documenting what already exists before designing changes:

1. **Existing data model**: What tables/collections exist? What are the key relationships?
2. **Existing API surface**: What endpoints or interfaces are already exposed?
3. **Existing component map**: What services, modules, or apps are already running?
4. **Conventions in use**: Naming patterns, error handling approaches, auth mechanisms, test patterns.
5. **Known constraints**: Technical debt, scaling limits, things that can't change easily.

If the user can point you at code, schemas, or docs, review them. Otherwise, ask them to describe the current state. Capture this in a "Current State" section at the top of the architecture note.

For greenfield projects, skip this section.

## What to Cover

### 1. Tech Stack Decisions
Languages, frameworks, databases, infrastructure. Justify each choice briefly — why this and not the obvious alternative.

If you know the user's existing stack, tools, or preferences (from memory or conversation), factor those in. Don't propose a stack that contradicts what they already use unless there's a strong reason, and call it out if so.

### 2. Data Model
Entity-relationship diagram showing all persistent data needed for MVP. Include relationships, cardinality, and key fields. Use a Mermaid ER diagram.

For brownfield: show both existing entities (marked) and new/modified entities.

### 3. Component Map
What are the major components (frontend, backend, services, external integrations)? Use SVG or Mermaid to show boundaries and communication paths.

### 4. API Boundaries
For each component boundary, describe the interface. Not full OpenAPI specs — just the shape: "the frontend calls the backend's REST API for CRUD on books and reading sessions; the backend pushes notifications via WebSocket."

### 5. Authentication & Authorization
How do users log in? What permissions model? Keep it proportional to the app's needs.

### 6. External Integrations
Any third-party services, APIs, or data sources. How do they connect?

### 7. Key Technical Decisions (ADRs)

Architecture Decision Records use the `[D-NNN]` ID prefix in design artifacts. Each ADR records a single architectural decision: the context, options considered, the choice, and the consequences.

**Each `[D-NNN]` has a one-to-one twin in the repo at `docs/adr/0NNN-<slug>.md`.** The vault entry exists for design-time traceability (linked from stories, acceptance criteria, the dependency graph); the repo entry is the durable record that future implementer and reviewer agents read. When you write `[D-007]` in a design note, also write `docs/adr/0007-postgres-write-model.md` in the repo using the format in [[language/grill-with-docs/references/ADR-FORMAT.md]].

Use Obsidian callouts (`> [!note] [D-NNN] Title`) or list-item headings to make the vault entries grep-able.

Only write an ADR when all three are true (from [[grill-with-docs]]):
1. Hard to reverse
2. Surprising without context
3. Result of a real trade-off

If any of the three is missing, skip the ADR — the decision is just a design note that lives in `Architecture.md`.

ADR IDs are permanent — if a decision is later revised, add a *new* ADR that supersedes the old one (cross-reference both directions) rather than editing the old in place. The history is more valuable than the cleanup.

Examples: "We'll use event sourcing for the reading log because…" or "SQLite is sufficient because…".

If the project uses **versioned database migrations** (or equivalent schema-evolution infrastructure), migrations use the `M-NNN` ID prefix (no brackets). Migration slots are **claimed at Phase 8 issue creation time, not at design time** — claiming a slot during design risks drift with in-flight branches that may merge migrations ahead of you. Design artifacts use the `M_NEXT` placeholder; Phase 8 substitutes the actual slot number when the issue file is created. See `references/promotion-cycle.md` for the procedural rationale.

### 8. Cross-Cutting Concerns

This is a required checklist. Address every item — even if the answer is "not needed for MVP, deferred." These concerns don't belong to any single feature but will cause pain if ignored:

| Concern | Address |
|---------|---------|
| **Error handling** | How are errors surfaced to users? How are they logged? What's the recovery path? |
| **Loading & empty states** | What does the user see while data loads? What about screens with no data yet? |
| **Offline behavior** | Does the app need to work offline? If so, what's the sync strategy? If not, how does it handle network loss gracefully? |
| **Logging & observability** | What gets logged? Where do logs go? Any metrics or health checks? |
| **Data migration** | How does the schema evolve over time? Migration tooling? For brownfield: how do we migrate existing data? |
| **First-run experience** | What happens the very first time a user opens the app? Onboarding, seed data, setup wizard? |
| **Backup & recovery** | How is data backed up? What's the recovery process if something goes wrong? |
| **Configuration** | What's configurable vs. hardcoded? Environment variables, config files, feature flags? |
| **Testing strategy** | Unit tests, integration tests, E2E? What coverage is expected? What's the test runner? |
| **CI/CD** | How does code get from commit to running? Pipeline stages, deployment targets. |

Not all of these need deep treatment. Some will be a single sentence ("Offline: not supported in MVP, app shows a connection-required message"). The point is to force the decision rather than discovering the gap during coding.

## What NOT to Cover
- Implementation details (file structure, class hierarchies, function signatures)
- Deployment infrastructure specifics (save for a future ops conversation)
- Performance optimization (premature at this stage unless there's a known constraint)

## Output: `{ProjectName}/Architecture.md`

```markdown
---
tags:
  - {project-tag}
  - design
  - architecture
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} Architecture
  - {ProjectName} Technical Design
---

## Current State (brownfield only)
{Description of existing system — data model, APIs, components, conventions}

## Tech Stack

| Layer | Choice | Rationale |
|-------|--------|-----------|
| Frontend | {framework} | {why} |
| Backend | {language/framework} | {why} |
| Database | {db} | {why} |
| {other layers} | ... | ... |

## Data Model

{Mermaid ER diagram}

## Component Map

{Mermaid or SVG diagram showing components and their communication}

## API Boundaries

### {Component A} → {Component B}
{Interface description}

## Authentication & Authorization
{Approach description}

## External Integrations
{If any}

## Key Technical Decisions

> [!note] [D-001] {Decision Title}
> {Context, decision, and brief rationale}

(The `[D-NNN]` ID must sit immediately after `[!note]` — that's how the validator recognises the line as an ADR definition. Without it, the decision won't register and downstream `[D-NNN]` references will fail orphan-checks.)

## Cross-Cutting Concerns

### Error Handling
{Approach}

### Loading & Empty States
{Approach}

### Offline Behavior
{Approach or "Not supported — connection required message on network loss"}

### Logging & Observability
{Approach}

### Data Migration
{Approach}

### First-Run Experience
{Approach}

### Backup & Recovery
{Approach}

### Configuration
{Approach}

### Testing Strategy
{Approach}

### CI/CD
{Approach}
```

## Gate
Ask: "Does this architecture make sense? Any technology choices you'd change? Any missing components? Take a look at the cross-cutting concerns — anything I've deferred that you think needs to be in MVP?"
