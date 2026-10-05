# Out-of-Scope Knowledge Base

The `.out-of-scope/` directory in the repo stores persistent records of rejected feature requests. Two purposes:

1. **Institutional memory** — why a feature was rejected, so the reasoning isn't lost when the issue is closed
2. **Deduplication** — when a new issue comes in matching a prior rejection, surface the previous decision instead of re-litigating it

## Directory structure

```
.out-of-scope/
├── dark-mode.md
├── plugin-system.md
└── graphql-api.md
```

One file per **concept**, not per issue. Multiple issues requesting the same thing are grouped under one file.

## File format

Write in a relaxed, readable style — more like a short design document than a database entry. Use paragraphs, code samples, and examples to make the reasoning clear to someone encountering it for the first time.

```markdown
# Dark Mode

This project does not support dark mode or user-facing theming.

## Why this is out of scope

The rendering pipeline assumes a single color palette defined in
`ThemeConfig`. Supporting multiple themes would require:

- A theme context provider wrapping the entire component tree
- Per-component theme-aware style resolution
- A persistence layer for user theme preferences

This is a significant architectural change that doesn't align with the
project's focus on content authoring. Theming is a concern for downstream
consumers who embed or redistribute the output.

\`\`\`ts
// The current ThemeConfig interface is not designed for runtime switching:
interface ThemeConfig {
  colors: ColorPalette; // single palette, resolved at build time
  fonts: FontStack;
}
\`\`\`

## Prior requests

- #42 — "Add dark mode support"
- #87 — "Night theme for accessibility"
- #134 — "Dark theme option"
```

### Naming

Use a short, descriptive kebab-case name for the concept: `dark-mode.md`, `plugin-system.md`. The name should be recognizable enough that someone browsing the directory understands what was rejected without opening the file.

### Writing the reason

Substantive — not "we don't want this" but why. Good reasons reference:

- Project scope or philosophy ("This project focuses on X; theming is a downstream concern")
- Technical constraints ("Supporting this would require Y, which conflicts with our Z architecture")
- Strategic decisions ("We chose to use A instead of B because…")

Durable. Avoid temporary circumstances ("we're too busy right now") — those aren't real rejections, they're deferrals.

## When to check `.out-of-scope/`

During triage (step 1: Gather context), read all files in `.out-of-scope/`. When evaluating a new issue:

- Check if the request matches an existing out-of-scope concept
- Matching is by concept similarity, not keyword — "night theme" matches `dark-mode.md`
- If there's a match, surface it to the maintainer: "This is similar to `.out-of-scope/dark-mode.md` — we rejected this before because [reason]. Do you still feel the same way?"

The maintainer may:

- **Confirm** — append the new issue to the existing file's "Prior requests" list, then close
- **Reconsider** — delete or update the out-of-scope file; the issue proceeds through normal triage
- **Disagree** — issues are related but distinct, proceed with normal triage

## When to write to `.out-of-scope/`

Only when an **enhancement** (not a bug) is rejected as `wontfix`. The flow:

1. Maintainer decides a feature request is out of scope
2. Check if a matching `.out-of-scope/` file already exists
3. If yes: append the new issue to the "Prior requests" list
4. If no: create a new file with the concept name, decision, reason, and first prior request
5. Post a comment on the issue explaining the decision and mentioning the `.out-of-scope/` file
6. Close the issue with the `wontfix` label

## Cross-reference with ADRs

Some `wontfix` decisions are also load-bearing architectural choices. If the rejection reason names a real trade-off that future architecture reviews shouldn't re-suggest, write an ADR in `docs/adr/` *in addition to* the `.out-of-scope/` file. The two serve different audiences:

- `.out-of-scope/` is for the issue tracker — "we already said no to this"
- ADR is for the codebase — "the architecture is shaped this way for these reasons"

## Updating or removing out-of-scope files

If the maintainer changes their mind about a previously rejected concept:

- Delete the `.out-of-scope/` file (or update it with a note that the decision was revisited)
- The skill does not need to reopen old issues — they're historical records
- The new issue that triggered the reconsideration proceeds through normal triage
