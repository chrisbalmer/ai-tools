# Phase 6: Dependency Graph & Sequencing

## Purpose
Map what blocks what. Determine build order. Identify the critical path and what can be parallelized.

## Process

### 1. Identify Dependencies Between Stories

A story depends on another if it cannot be started or completed without the other's output. Common dependency types:
- **Schema dependency**: Story B needs a database table that Story A creates
- **API dependency**: Story B calls an endpoint that Story A builds
- **Component dependency**: Story B uses a UI component that Story A creates
- **Data dependency**: Story B needs seed data or configuration that Story A sets up

Not every logical ordering is a hard dependency. If two stories touch different parts of the same file but don't depend on each other's output, they can be parallelized (with a merge step).

### 2. Build the Dependency Graph

Use a Mermaid flowchart showing story IDs, titles, and their dependencies. Group by epic for readability. Use subgraphs for epics.

### 3. Determine Build Phases

Group stories into sequential phases where:
- All stories in a phase can be worked on in parallel (or sequentially — Claude Code typically works one issue at a time)
- All dependencies from prior phases are satisfied
- Each phase produces something testable or demonstrable

### 4. Identify the Critical Path

The longest chain of dependent stories from start to finish. This determines the minimum number of sequential steps regardless of parallelization.

### 5. Suggest Milestones

After which phases do you have something demonstrable? Where are natural "checkpoint" moments where the user can try the app and give feedback? Good milestones are:
- First time something renders on screen
- First time data round-trips (create → save → reload → display)
- First time a complete user flow works end-to-end
- Feature-complete MVP (all stories done)

## Output: `{ProjectName}/Dependency Graph.md`

```markdown
---
tags:
  - {project-tag}
  - design
  - dependencies
  - sequencing
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} Dependencies
  - {ProjectName} Build Order
---

## Dependency Graph

{Mermaid flowchart showing story dependencies, grouped by epic}

## Build Phases

### Phase 1: Foundation
{List of stories with no dependencies — scaffolding, schemas, base config}

**Milestone:** {What's demonstrable after this phase}

### Phase 2: {Phase Name}
{Stories unlocked by Phase 1}
**Depends on:** Phase 1
**Milestone:** {What's demonstrable}

{...continue for all phases}

## Critical Path

{The longest dependency chain listed step by step}

> [!info] Minimum Sequential Steps
> {Count} stories on the critical path. Everything else can be worked in parallel around this chain.

## Parallelization Opportunities

{Stories within each phase that have no dependencies on each other and could theoretically be worked simultaneously}
```

## Gate
Ask: "Does this build order make sense? Would you rearrange any of the phases? Are the milestones at the right points — do you want to be able to try the app earlier or later than where I've placed checkpoints?"
