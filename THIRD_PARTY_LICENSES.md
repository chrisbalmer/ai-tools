# Third-party licenses and attributions

This repository is licensed under the MIT License (see [`LICENSE`](./LICENSE)). Several skills in it are adapted from [mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock, also licensed under the MIT License (full text below); those files remain subject to that notice.

## Skills adapted from mattpocock/skills

Upstream links are pinned to commit [`694fa30`](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f) (2026-06-10), the last upstream revision where all seven source paths exist under `skills/engineering/`. Several have since been renamed, merged, or removed upstream (e.g. `to-prd` and `to-issues` became `/to-spec` and `/to-tickets`), so unpinned links 404.

The following skills are direct ports — adapted to this repo's conventions and to Gitea (where Matt's originals were tool-agnostic or GitHub-shaped), but the core structure, philosophy, and content originate from Matt Pocock's work:

| Skill in this repo | Originates from | Notes |
|---|---|---|
| [`skills/language/grill-with-docs/`](./skills/language/grill-with-docs/) | [engineering/grill-with-docs](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f/skills/engineering/grill-with-docs) | `SKILL.md`, `references/CONTEXT-FORMAT.md`, `references/ADR-FORMAT.md` adapted; expanded with vault/repo split guidance |
| [`skills/language/improve-codebase-architecture/`](./skills/language/improve-codebase-architecture/) | [engineering/improve-codebase-architecture](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f/skills/engineering/improve-codebase-architecture) | `SKILL.md`, `references/LANGUAGE.md`, `references/INTERFACE-DESIGN.md` adapted; `references/DIAGRAMS.md` rewritten for in-repo markdown output (Matt's version produced HTML in a temp dir) |
| [`skills/plan/to-prd/`](./skills/plan/to-prd/) | [engineering/to-prd](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f/skills/engineering/to-prd) | `SKILL.md` adapted; retargeted from generic tracker to Gitea, expanded `CONTEXT.md` reading discipline |
| [`skills/plan/to-issues/`](./skills/plan/to-issues/) | [engineering/to-issues](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f/skills/engineering/to-issues) | `SKILL.md` adapted; retargeted to Gitea, dependency-link format matches `milestone-builder` parsing |
| [`skills/execute/tdd/`](./skills/execute/tdd/) | [engineering/tdd](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f/skills/engineering/tdd) | `SKILL.md` and all references (`references/tests.md`, `mocking.md`, `deep-modules.md`, `interface-design.md`, `refactoring.md`) adapted; cross-referenced with this repo's `improve-codebase-architecture/references/LANGUAGE.md` |
| [`skills/execute/diagnose/`](./skills/execute/diagnose/) | [engineering/diagnose](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f/skills/engineering/diagnose) | `SKILL.md` adapted with light edits |
| [`skills/plan/triage/`](./skills/plan/triage/) | [engineering/triage](https://github.com/mattpocock/skills/tree/694fa30311e02c2639942308513555e61ee84a6f/skills/engineering/triage) | `SKILL.md`, `references/AGENT-BRIEF.md`, `references/OUT-OF-SCOPE.md` adapted; retargeted from generic tracker to Gitea, label mapping moved to per-repo `MEMORY.md` |

## Skills original to this repo

The following are not derived from Matt's work and are not covered by his license:

- `skills/plan/app-design/`
- `skills/execute/ship-issue/`
- `skills/execute/milestone-builder/`
- `skills/execute/milestone-e2e-test/`
- `skills/execute/review/` (the Reviewer procedure; consumes the Review packet from the `review-prep` Utility agent)
- `skills/general/obsidian-note/`
- `skills/general/session-note/`
- `skills/general/op-secrets/`
- `skills/general/har/` (including `scripts/sanitize-har.py` and `scripts/har-digest.py`)
- `agents/` (Utility agent definitions: `commit`, `ci-check`, `test-run`, `tracker-read`, `review-prep`)
- Repo-level docs and manifests: `CONTEXT.md`, `MODELS.md`, `WORKFLOW.md`, `README.md`, `CLAUDE.md`, `.claude-plugin/`

Edits made to those skills during this project (wiring `CONTEXT.md` into implementer/reviewer briefs, etc.) are conventional adoption of patterns established by the ported skills, not direct ports.

## MIT License (mattpocock/skills)

```
MIT License

Copyright (c) 2026 Matt Pocock

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
