# Phase 1: Vision

## Purpose
Capture what the ideal version of the application looks like without constraints. No planning, no architecture, no technology choices — just describe the experience.

## Setup

Before diving into the vision, establish the project:

1. Confirm or ask for the **project name**
2. Ask: **"Where should I place the {ProjectName} directory?"** (e.g., `/path/to/vault/Apps/`)
3. Determine **greenfield or brownfield**:
   - Greenfield: "Describe the ideal app from scratch"
   - Brownfield: "What are we adding to the existing app? Point me at any existing code, docs, or schemas."

All files for this project will be created inside `{base-path}/{ProjectName}/`.

## How to Prompt

For greenfield projects, if the user hasn't already provided a vision:

> "If time and labor were not a consideration, what would the optimal version of this application look like? Don't plan — just describe. What does it do? What does the user experience? What problems does it solve completely?"

For brownfield projects:

> "Describe the features you want to add. What should the app do that it doesn't do today? What existing behavior should change?"

If the user has already shared a vision (possibly from a prior conversation), summarize it back and ask if it's complete.

## Iteration

After the initial vision dump, help the user refine by asking probing questions:
- "What's missing? What would make this feel magical?"
- "Who are the different types of users? What does each one care about most?"
- "What's the thing that would make someone choose this over pen-and-paper or a spreadsheet?"
- "Are there any non-obvious features — things that aren't the core purpose but would make the app feel complete?"

Don't interrogate. If the user gives a rich description, you might only need one or two follow-ups. Read the room.

## Assigning Feature IDs

After the vision is agreed upon, assign `[V-NNN]` IDs to each distinct feature or capability mentioned. Group related sub-features under a parent. Present the tagged list for confirmation.

IDs are permanent — they never change once assigned, even if features are reordered or removed later.

## Seed the domain glossary

The vision conversation is the first place domain terms emerge. As the user names the concepts the app revolves around — *Book*, *Reading Session*, *Reader*, *Shelf* — seed them into a `CONTEXT.md` file using the [[grill-with-docs]] discipline.

**Where to write it during Phase 1:**

- **Greenfield**: no repo exists yet. Create `{ProjectName}/CONTEXT.md` in the vault alongside `Vision.md`. The file moves to the project repo at Phase 4 when the repo is created.
- **Brownfield**: the repo already exists. Read the repo's `CONTEXT.md` and `docs/adr/` first (the user should point you at the repo path), and update *that* file as terms emerge. Do not duplicate the glossary into the vault.

Apply [[grill-with-docs]] discipline as you go:

- Sharpen fuzzy or overloaded terms before locking them in (Customer vs. User, Order vs. Cart, etc.)
- One or two sentences per term — what it IS, not what it does
- For each term, list `_Avoid_:` aliases the user mentioned but you're not using
- Only domain-specific terms; not general programming concepts

You do not need a full glossary at Phase 1 end — just the terms that appear in the vision. More will land in Phase 2 (acceptance criteria) and Phase 4 (architecture).

See [[language/grill-with-docs/references/CONTEXT-FORMAT.md]] for the format.

## Output: `{ProjectName}/Vision.md`

```markdown
---
tags:
  - {project-tag}
  - design
  - vision
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} Vision
---

## Overview

{2-3 paragraph narrative description of the application's purpose and experience}

## Feature Map

### [V-001] {Feature Name}
{Description of what this feature does from the user's perspective}

### [V-002] {Feature Name}
{Description}

{...continue for all features}

## User Personas

### {Persona Name}
{Who they are, what they need, how they use the app}

## Out of Scope
{Anything explicitly excluded during the vision conversation}
```

For brownfield projects, add a section before the Feature Map:

```markdown
## Current State
{Brief description of what exists today — key capabilities, known limitations, relevant technical context}
```

## Gate
Ask: "Does this vision document capture what you want to build? Anything missing or wrong before we lock it in and write acceptance criteria?"

Wait for explicit approval. If they have changes, incorporate them and re-present.
