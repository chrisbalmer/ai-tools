# Development Workflow

A practical manual for building software using the skills in this repo. Read this before starting a new project, or if you already have a project that's getting tangled and you're not sure which skill to reach for.

## Mental model

The skills break into three layers. Most large-project headaches come from missing the **language** layer entirely — using only the **plan** and **execute** layers compounds entropy because every agent works in a context-poor environment.

| Layer | Purpose | Skills |
|---|---|---|
| **Language** | Build and maintain shared vocabulary and decisions that travel with the code | `/grill-with-docs`, `/improve-codebase-architecture` |
| **Plan** | Turn intent into structured, slicable work | `/app-design` (heavy, greenfield), `/to-prd` + `/to-issues` (lightweight, brownfield), `/triage` |
| **Execute** | Take an issue from "ready to ship" to "merged" | `/ship-issue` (one issue), `/milestone-builder` (many issues in dependency order), `/review`, `/tdd`, `/diagnose`, `/milestone-e2e-test` |

The **language** layer is the contract every other skill depends on. `CONTEXT.md` (domain glossary) and `docs/adr/` (architectural decisions) live **in the repo**, not in the Obsidian vault, because every implementer and reviewer agent needs to read them. The vault is for *thinking-time* artifacts (vision, acceptance criteria, wireframes, stories); the repo is for *living* artifacts (glossary, decisions, architecture review reports) plus the **Design bundle** (Comps, prototype, screenshots) so implementer and reviewer agents can read it.

If you take one thing from this manual: **never let an implementer agent loose on a repo without a `CONTEXT.md`.** That's the single biggest failure mode in agent-driven development.

## Vault vs. repo split

| Artifact | Where it lives | Why |
|---|---|---|
| Vision, acceptance criteria, wireframes, stories, dependency graph, design review | Obsidian vault | Design-time thinking; the repo doesn't exist yet for greenfield, or the design is fleeting and shouldn't bloat the repo for brownfield |
| Design bundle (`design_handoff_<project>/`) | Repo | Comps (screenshots + prototype) live in the repo so implementer/reviewer agents can `Read` them from worktrees |
| `CONTEXT.md` (glossary) | Repo root | Every implementer / reviewer agent reads this. Travels with the code. |
| `docs/adr/0NNN-<slug>.md` | Repo | Decisions an agent must not re-litigate. Numbered, sequential, durable. |
| `docs/architecture-review-<date>.md` | Repo | Versioned record of architectural reviews — diffable across time |
| Issue bodies, agent briefs | Gitea tracker | The actual contract that produces a PR |
| `.out-of-scope/<concept>.md` | Repo | "We already said no to this" — checked during triage |

`CONTEXT.md` is **born in the vault** during `/app-design` Phase 1–2 as terms emerge, then **moves to the repo** when the repo is created (typically Phase 4). After that, the repo is canonical.

## Greenfield workflow (new app from scratch)

```
Vision
  ↓ /app-design Phase 1   (vision; seed CONTEXT.md in vault)
  ↓ /app-design Phase 2   (acceptance criteria; sharpen CONTEXT.md)
  ↓ /app-design Phase 3   (wireframes + Design bundle — skip if backend-only)
  ↓ /app-design Phase 4   (architecture; create repo; MOVE CONTEXT.md TO REPO; seed docs/adr/)
  ↓ /app-design Phase 5   (stories; UJTs)
  ↓ /app-design Phase 6   (dependency graph)
  ↓ /app-design Phase 7   (design review — fresh session, not the author)
  ↓ /app-design Phase 8   (issues — gated by validator including `vocab` check)
  ↓ /milestone-builder    (fan out parallel implementers in dependency order)
  ↓ /milestone-e2e-test   (visual validation; bugs routed through /diagnose)
  ↓ User reviews and merges milestone PR → main
```

Each implementer spawned by `/milestone-builder` reads `CONTEXT.md` and the relevant ADRs as part of its brief. Reviewer subagents flag vocabulary drift as a Blocker, not a nit.

**Between milestones** (before starting the next one): run `/improve-codebase-architecture`. Parallel implementer fan-out degrades architecture silently — this is where you catch the entropy before it compounds.

## Brownfield workflow (adding a feature to an existing app)

Two paths depending on the size of the change.

### Lightweight path (small to medium feature)

```
/grill-with-docs     (sharpen vocabulary; update CONTEXT.md, drop ADRs)
  ↓ /to-prd          (synthesize the PRD; publish to Gitea as parent issue)
  ↓ /to-issues       (slice the PRD into vertical-slice sub-issues)
  ↓ /triage          (apply ready-for-agent labels; write agent briefs)
  ↓ /ship-issue      (per slice — or /milestone-builder if grouped)
```

Skip `/grill-with-docs` only if the conversation is already crisp. If you're tempted to skip but the user keeps using fuzzy terms, do not skip — the implementer brief will be fuzzy too.

### Heavy path (major brownfield expansion)

Use the full `/app-design` greenfield workflow above. Phase 1 starts with "what are we adding?" rather than "describe the whole app," and Phase 4 starts with documenting the current state of the existing code. `CONTEXT.md` and `docs/adr/` already exist; read them at Phase 1 and update them in place.

**Heuristic:** if the change touches enough surface area that Phases 5–6 (story decomposition + dependency graph) would produce a meaningful diagram, use the heavy path. Otherwise lightweight is right.

## Bug workflow

```
/triage              (classify, attempt reproduction, write brief)
  ↓ /diagnose        (build deterministic feedback loop; hypothesize; fix with regression test)
  ↓ /ship-issue      (apply the fix as a regular issue flow)
```

If the bug surfaced during `/milestone-e2e-test`, it follows the same path — `/milestone-e2e-test`'s bug workflow routes non-trivial bugs through `/diagnose` rather than jumping straight to a fix.

If the diagnosis surfaces architectural friction (no good seam for the regression test, hidden coupling, tangled callers), hand off to `/improve-codebase-architecture` **after** the fix is in, not before.

## Triage workflow

The state machine that keeps the tracker honest:

```
(new issue) → needs-triage → {needs-info, ready-for-agent, ready-for-human, wontfix}

needs-info → needs-triage (after reporter replies)

ready-for-agent → /ship-issue or /milestone-builder

wontfix (enhancement) → .out-of-scope/<concept>.md
wontfix (bug) → polite explanation, close
```

`/ship-issue` and `/milestone-builder` **refuse to start** if an issue is still `needs-triage` or `needs-info`. Run `/triage` first.

## Example: redesigning a UI layout on a live app

UI redesigns are the most common brownfield change once you start *using* the app you built. The trigger is usually vague — "this screen feels cluttered," "I keep hitting the wrong button," "these two views should really be one." Two things make UI redesigns different from backend feature work:

1. **The visual is the spec.** Prose acceptance criteria carry the *behavior* contract but not the layout. You need a visual loop (screenshots, the browser MCP, or live use of the app) in addition to the test loop.
2. **Existing UJTs are at risk.** If the redesign moves or renames screen elements, the UJTs in the vault that touch those elements need re-authoring. A redesign that ships without updating UJTs leaves the validation gate silently broken.

### Step 1 — Scope the redesign

Open a fresh session in the app's repo (`~/code/<app>`) and decide which path applies:

| Scope | Signal | Path |
|---|---|---|
| **Small** | One screen or component; navigation unchanged; no new domain concepts | Lightweight brownfield (skip ahead to Step 3) |
| **Large** | Multiple screens; navigation restructure; new mental model the user has to learn | Re-enter `/app-design` at Phase 3 (Wireframes) — update the wireframes and the affected stories before slicing |

If you're unsure, default to **Small** and let the grilling session in Step 2 surface whether the change is actually larger than you thought.

### Step 2 — Grill what's wrong

UI complaints arrive vague. The grilling session sharpens them before any redesign sketch lands. Fresh session in `~/code/<app>`:

```
I want to redesign a UI layout in <App>. The trigger: <one or two sentences
describing what's wrong with the current layout, in your own words — e.g.,
"the reading log screen has 6 collapsible sections and I never find what
I'm looking for">.

Run /grill-with-docs against the existing UI. Read:
  - ~/code/<app>/CONTEXT.md for the domain vocabulary I should use to
    describe screen elements
  - The relevant wireframe(s) in
    <vault>/Apps/<App>/Wireframes.md (or
    Wireframes/<ScreenName>.md if split)
  - The relevant UJT(s) under
    <vault>/Apps/<App>/User Journey Tests/
  - The actual component code (use Explore subagent if helpful)

Grill me on:
  - What specifically is failing — discoverability, click depth, visual
    hierarchy, error states, mobile?
  - Who's the affected user (which persona from Vision.md)?
  - What's the desired outcome stated as an observable behavior, not as
    "make it look nicer"?
  - Are any new domain concepts emerging from how I'd describe the redesign
    (e.g., a "quick view" vs. "detail view" split that doesn't exist in
    CONTEXT.md yet)?

Update CONTEXT.md inline if new vocabulary lands. At the end, tell me
whether this looks like a Small or Large redesign per the scoping table
in the skill set's WORKFLOW.md.
```

### Step 3 — For Small redesigns, lightweight path with visual loop

```
The redesign is Small. Run /to-prd to synthesize a PRD covering:
  - Current behavior (with a description of the screen layout I just grilled)
  - Desired behavior (using CONTEXT.md vocabulary; describe the layout in
    text — element ordering, grouping, what's primary vs. secondary)
  - Acceptance criteria that are visually verifiable (e.g., "the
    Reading Sessions panel appears above the Status Bar; clicking a
    record opens a detail drawer rather than a new screen")
  - Out of scope (explicit: what's NOT moving or changing)

Publish to Gitea with ready-for-agent. Then /to-issues to slice. Prefer
one or two thin slices over one large one — UI work benefits from
seeing the change land incrementally so I can react to each.

After slicing, do NOT ship yet — I want to do a visual sketch first
(see Step 4 of the UI redesign flow in WORKFLOW.md).
```

### Step 4 — Sketch before implementing (optional but recommended)

Before spawning the Implementer for the actual implementation, drop into a sketch session — either pencil/Figma if you have it, or an ascii layout in a scratch note. The cost is 10 minutes; the cost of having the Implementer build a layout you then hate is much higher.

If you want the agent to help, fresh session:

```
Sketch 2–3 different layouts for the redesigned <screen name> in <App>,
based on the PRD at Gitea issue #<NNN>. For each variant, produce an ascii
mockup or describe the layout in enough detail that I can picture it:
  - Element ordering top-to-bottom
  - Grouping (which elements share a container, which are floating)
  - Primary vs. secondary affordances
  - Mobile behavior (does it stack, hide, or remain side-by-side?)

Make the variants meaningfully different — not three flavors of the same
idea. One should optimize for "minimum chrome, maximum content"; one for
"clear hierarchy with visible structure"; one for whatever third axis
seems most relevant to the redesign trigger.

Recommend which you'd ship and why. Use CONTEXT.md vocabulary for element
names.
```

> [!note] No `/prototype` skill yet
> Matt Pocock's skill set has a `/prototype` skill for runnable UI variants behind a toggleable route. That's not currently ported into this repo. If UI redesigns become frequent on an app, consider porting it — it sits between Step 4 (sketch) and Step 5 (ship) and lets you actually click through variants before committing. Until then, the ascii sketch is the cheap stand-in.

### Step 5 — Ship the slice(s) with visual validation

```
Ship issue #<NNN> via /ship-issue. The implementer brief MUST include:
  - Read CONTEXT.md and any ADRs in docs/adr/ touching the UI layer
  - The variant from the sketch session that I approved (paste the ascii
    sketch into the brief)
  - Visual acceptance: after the change ships, the implementer takes a
    screenshot via the browser MCP (mcp__claude-in-chrome__*) showing the
    new layout, and includes the screenshot in the PR-back report
  - UJT update: if the redesign changes selectors, element ordering, or
    screen affordances that any UJT under
    <vault>/Apps/<App>/User Journey Tests/ exercises,
    the implementer updates the UJT prose in the same PR. Do NOT merge a
    PR that leaves a UJT pointing at the old layout.

Standard /ship-issue gates apply: CI → Reviewer → merge. The reviewer
should additionally scrutinize whether the screenshot matches the sketch
variant — visual drift between sketch-and-shipped is the failure mode
specific to UI work.
```

### Step 6 — Live use, then loop

After merge, **actually use the app** for a few sessions before declaring the redesign done. UI redesigns reveal their real problems only after live use, not after the screenshot looks right. If you find new friction, route it back through Step 2 (re-grill) with the new complaint — don't try to patch piecemeal.

### When to invoke `/milestone-e2e-test` for UI redesigns

If the redesign spans 3+ slices that ship over a milestone branch, run `/milestone-e2e-test` before merging the milestone to main. The browser-based validation catches visual regressions that PR-level screenshot checks miss — especially interaction bugs that only appear when the redesigned components compose with the rest of the app.

## Continuous architecture

After every 5–10 PRs (or between milestones), run `/improve-codebase-architecture`. The skill explores the repo, identifies shallow modules and leaky seams, and proposes deepening candidates. You pick which to land; it drops into a grilling loop on the candidate; the result becomes vertical-slice issues for `/ship-issue`.

This is the **single most important habit** for keeping a long-lived agent-driven project healthy. Without it, parallel implementer fan-out degrades architecture silently and the codebase becomes a ball of mud you can't reason about.

## Which skill for which situation

| Situation | Skill |
|---|---|
| "I have an app idea" | `/app-design` Phase 1 (greenfield) |
| "I want to add a feature to existing app" — small | `/grill-with-docs` then `/to-prd` then `/to-issues` |
| "I want to add a feature to existing app" — large | `/app-design` greenfield workflow (brownfield mode) |
| "I want to redesign a UI layout on an existing screen" | `/grill-with-docs` → sketch session → `/to-prd` → `/to-issues` → `/ship-issue` with screenshot gate (see [Example: redesigning a UI layout](#example-redesigning-a-ui-layout-on-a-live-app)) |
| "Let's stress-test this plan against the codebase" | `/grill-with-docs` |
| "The codebase is getting messy" | `/improve-codebase-architecture` |
| "Ship this issue end-to-end" | `/ship-issue <N>` |
| "Build this whole milestone" | `/milestone-builder` |
| "Review this PR against the spec / is #N ready to merge" | `/review <PR>` (invoked automatically from `/ship-issue` and `/milestone-builder` Stage 3) |
| "Validate the milestone before merging" | `/milestone-e2e-test` |
| "Something is broken / write me a regression test" | `/diagnose` |
| "Test-drive this new behavior" | `/tdd` (usually invoked by `/ship-issue`'s implementer brief automatically) |
| "What needs my attention in the tracker" | `/triage` |
| "Move #N to ready-for-agent" | `/triage` |
| "Create a note in my Obsidian vault" | `/obsidian-note` |
| "Save this session as a note / summarize what we did" | `/session-note` |
| "Call this API with my key from 1Password" | `/op-secrets` |
| "Here's a HAR / what endpoint does the UI actually call / sanitize this capture" | `/har` |

## What changed from the old workflow

The skills used to be three: `/app-design`, `/milestone-builder`, `/ship-issue`. That covered **plan** and **execute** but missed the **language** layer entirely. The failure mode on large, long-lived projects was:

1. `/app-design` produced great issues in Obsidian
2. Implementers worked in repos with no `CONTEXT.md`, no ADRs
3. Each PR introduced ad-hoc vocabulary
4. After a few milestones, the codebase had several names for the same concept and several different ways of doing the same thing
5. Bugs accumulated; root causes pointed at architectural mush; no tool existed to surface or fix it

The seven new skills (`/grill-with-docs`, `/to-prd`, `/to-issues`, `/tdd`, `/diagnose`, `/improve-codebase-architecture`, `/triage`) fill the gaps:

- `/grill-with-docs` builds and maintains `CONTEXT.md` + ADRs as the contract every other skill reads from
- `/to-prd` + `/to-issues` give a lighter path for brownfield features so the 8-phase funnel isn't the only tool
- `/tdd` + `/diagnose` impose feedback-loop discipline at the implementer level
- `/improve-codebase-architecture` keeps architecture from compounding into mud
- `/triage` is the gate that keeps the tracker honest and ensures implementers are never under-briefed

The implicit contract throughout: **the codebase is authoritative**. The vault holds frozen design-time thinking; the repo holds the living language.

## Quick reference: file conventions

```
<repo>/
├── CONTEXT.md                              ← domain glossary (born in vault, moves here at Phase 4)
├── CONTEXT-MAP.md                          ← only if the repo has multiple bounded contexts
├── docs/
│   ├── adr/
│   │   ├── 0001-<slug>.md                  ← architectural decisions
│   │   └── 0002-<slug>.md
│   └── architecture-review-<date>.md       ← /improve-codebase-architecture reports
├── design_handoff_<project>/                ← Design bundle (Phase 3; UI projects only)
│   ├── README.md                            ← full spec: screens, tokens, interactions
│   ├── screenshots/                         ← numbered PNGs — visual targets for each screen
│   ├── prototype/                           ← interactive HTML/JSX — token & structure source
│   └── docs/                                ← art style guide, architecture one-pager
├── .out-of-scope/
│   └── <concept>.md                        ← rejected feature requests (institutional memory)
├── CLAUDE.md                               ← project-specific instructions for Claude Code
├── MEMORY.md                               ← repo conventions Claude remembers across sessions
└── src/
```

```
<obsidian-vault>/<ProjectName>/
├── Vision.md                               ← Phase 1
├── Acceptance Criteria/
│   └── <FeatureName>.md                    ← Phase 2
├── Wireframes.md                           ← Phase 3 (optional)
├── Architecture.md                         ← Phase 4 (references docs/adr/ in the repo)
├── Stories/
│   └── <EpicName>.md                       ← Phase 5
├── User Journey Tests/
│   └── <JourneyName>.md                    ← Phase 5 (UI projects only)
├── Dependency Graph.md                     ← Phase 6
├── Design Review.md                        ← Phase 7
└── Issues/
    └── NN - S-NNN - <ShortTitle>.md        ← Phase 8 (markdown for direct Gitea import)
```

## When this workflow is the wrong fit

These skills are designed around an agent-driven workflow on a Gitea-tracked repo with Claude Code in the main thread. They are less suited to:

- **Solo prototyping** where you'll throw the code away in a week. Drop the heavy plan layer; just write the code, and reach for `/grill-with-docs` only if you want shared vocabulary later.
- **Repos using GitHub instead of Gitea.** Skills with MCP calls (`mcp__gitea__*`) will need adaptation. The patterns transfer; the API calls don't.
- **Codebases where you're not the architect.** `/improve-codebase-architecture` and `/grill-with-docs` assume you have authority to update `CONTEXT.md` and land ADRs. If you're contributing to someone else's project, skip those and use the lightweight execute layer (`/ship-issue` against well-specified issues you've been handed).
