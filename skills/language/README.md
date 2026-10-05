# Language layer

Skills that build and maintain the shared vocabulary and decisions that travel with the code. The foundation every other skill reads from — without this layer, parallel agent fan-out compounds entropy because every implementer works in a context-poor environment.

| Skill | Purpose |
|---|---|
| [`grill-with-docs`](./grill-with-docs/SKILL.md) | Interview the user about a plan, design, or change — challenging it against `CONTEXT.md` and `docs/adr/`, updating both inline as decisions crystallize. The primary author of the project's domain glossary and ADRs. |
| [`improve-codebase-architecture`](./improve-codebase-architecture/SKILL.md) | Surface architectural friction and propose **deepening opportunities** — refactors that turn shallow modules into deep ones. Writes a markdown report to `docs/architecture-review-<date>.md`. Run between milestones to catch entropy before it compounds. |

See [`WORKFLOW.md`](../../WORKFLOW.md) for how the language layer composes with the plan and execute layers.
