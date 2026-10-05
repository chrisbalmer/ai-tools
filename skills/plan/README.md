# Plan layer

Skills that turn intent into structured, sliceable work. The bridge between the language layer (`CONTEXT.md`, ADRs) and the execute layer (`ship-issue`, `milestone-builder`).

| Skill | Purpose |
|---|---|
| [`app-design`](./app-design/SKILL.md) | Heavy 8-phase design funnel for greenfield apps and major brownfield expansions. Vision → acceptance criteria → wireframes → architecture → stories → dependency graph → design review → issues. Produces Obsidian notes at each phase. |
| [`to-prd`](./to-prd/SKILL.md) | Lightweight brownfield path — synthesize the current conversation into a single PRD and publish it as a Gitea issue. No interview; assumes the idea has already been grilled. |
| [`to-issues`](./to-issues/SKILL.md) | Break a PRD or plan into independently-grabbable issues using **vertical-slice (tracer-bullet)** decomposition. |
| [`triage`](./triage/SKILL.md) | Move Gitea issues through a state machine of triage roles. The gate `ship-issue` and `milestone-builder` expect — both refuse to start if an issue is still `needs-triage`. |

See [`WORKFLOW.md`](../../WORKFLOW.md) for greenfield vs. brownfield path selection.
