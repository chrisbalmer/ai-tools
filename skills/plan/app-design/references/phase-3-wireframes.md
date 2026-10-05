# Phase 3: Wireframes & Screen Inventory

## Purpose
Map out every screen the MVP needs and how users navigate between them. Catch UX contradictions before they become architecture or story problems. This phase is optional for backend-only or headless projects — ask the user if they want to skip it.

## Scope
Only cover screens required by `mvp`-tagged acceptance criteria from Phase 2. If a screen only serves `v2` or `future` criteria, note its existence but don't design it.

## Process

### 1. Screen Inventory

Start by listing every distinct screen or view the app needs. For each screen, identify:
- Screen ID: `[SCR-NNN]`
- Name (e.g., "Book Detail", "Reading Log", "Dashboard")
- Which acceptance criteria it serves (e.g., `[AC-001]`, `[AC-003]`)
- Key elements visible on screen (data displayed, actions available, inputs)
- Entry points (how does the user get here?)

### 2. Navigation Flow

Build a Mermaid flowchart showing how screens connect. Include:
- Primary navigation paths (the happy path)
- Secondary paths (back buttons, breadcrumbs, deep links)
- Modal/overlay screens (indicate these differently from full screens)
- Entry points from outside the app (notifications, direct URLs)

### 3. Wireframe Layouts

For each screen, create a rough wireframe using SVG or Mermaid. These are structural layouts, not pixel-perfect designs:
- Show regions: header, nav, content zones, action areas
- Label what goes in each region (data fields, buttons, lists)
- Indicate interactive elements (tappable, editable, scrollable)
- Show key states: empty state, loaded state, error state (at minimum note which states exist)

Use SVG for wireframes — Mermaid doesn't handle spatial layouts well. Keep them schematic: boxes, labels, and arrows. No colors, no styling, no polish.

### 4. Cross-Screen Patterns

Identify patterns that repeat across screens:
- Common navigation (tab bar, sidebar, header)
- Shared components (search bars, filter panels, card layouts)
- Consistent interaction patterns (swipe to delete, pull to refresh, long press)

Documenting these now prevents inconsistency in stories later.

### 5. Comp Production (visual source of truth)

Wireframes capture structure; Comps capture the approved visual. For every MVP screen, produce a high-fidelity rendered Comp as files in a Design bundle directory (`design_handoff_<project>/`) in the repo: prototype HTML/JSX with realistic content, final color/typography/spacing choices, and key states (empty, loaded, error), plus screenshot PNGs of each rendered screen. The Comp is the **visual source of truth** that flows downstream:

- **Implementers** `Read` the Comp files — screenshots for visual targets, prototype source for tokens and structure (referenced in the issue's `## Comp Reference`)
- **Reviewers** run a Visual diff gate — screenshot of the running app vs. the Comp screenshot — before approving any PR that touches UI
- **E2E testing** (`/milestone-e2e-test`) includes a per-screen Comp diff pass

Comp conventions:
- One screenshot per screen (or per distinct state if a screen has substantially different empty/loaded/error appearances), named `NN-<screen-name>.png`
- Prototype HTML/JSX organized by component (e.g., `prototype/home.jsx`, `prototype/results.jsx`)
- A `README.md` in the bundle root with the full spec: screen inventory, per-screen layout details, design tokens, interaction notes, data shapes
- Use realistic sample data, not lorem ipsum — sample data exposes layout edge cases (long names, zero counts, missing optional fields)
- Include interactive states when they affect layout: expanded/collapsed sections, active/hover button states, validation errors
- Note the bundle directory path in the Wireframes.md screen entry for cross-reference

If the project uses an external design tool (Figma, Sketch), export the rendered frames as PNGs into the `screenshots/` directory. The skill doesn't mandate the tool; it mandates the rendered output committed to the repo.

For backend-only or headless projects, skip this step (no screens = no Comps).

## Output: `{ProjectName}/Wireframes.md`

```markdown
---
tags:
  - {project-tag}
  - design
  - wireframes
  - ui
created: {YYYY-MM-DD}
aliases:
  - {ProjectName} Wireframes
  - {ProjectName} Screens
---

## Screen Inventory

| Screen | ID | Serves | Key Elements |
|--------|-----|--------|-------------|
| {name} | [SCR-001] | [AC-001], [AC-003] | {elements} |
| {name} | [SCR-002] | [AC-002] | {elements} |

## Navigation Flow

{Mermaid flowchart showing screen connections}

## Screen Layouts

### [SCR-001] {Screen Name}

**Serves:** [AC-001], [AC-003]
**Entry points:** {how users arrive here}

{SVG wireframe layout}

**Comp:** see `design_handoff_<project>/screenshots/NN-<name>.png` + `prototype/<component>.jsx`

**States:**
- **Empty:** {what shows when no data exists}
- **Loaded:** {normal state}
- **Error:** {what shows on failure}

**Notes:** {interaction details, edge cases}

### [SCR-002] {Screen Name}
{...same structure}

## Shared Patterns

### Navigation
{Common nav elements and behavior}

### Reusable Components
{Components that appear on multiple screens}
```

## Gate

Present the screen inventory, navigation flow, wireframes, and rendered Comps. Ask:

"Do these screens cover everything the MVP needs? Is the navigation between them intuitive? Any screens missing, or screens here that shouldn't be? Do the Comps match your visual intent for each screen?"

Pay attention to acceptance criteria that don't map to any screen — either the criteria needs a screen, or it's purely backend (which is fine, but confirm). Also verify that every MVP screen in the inventory has a rendered Comp — if one is missing, the Design bundle is incomplete.
