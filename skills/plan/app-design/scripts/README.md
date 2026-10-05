# scripts/

Validation helpers for app-design projects. Stdlib only, Python 3.11+.

## `validate.py`

Runs structural checks against a project directory produced by the app-design skill. Operates on the markdown only — no parsing of code, schemas, or anything outside the design artifacts.

### Subcommands

```
python validate.py traceability  <project-path>
python validate.py ids            <project-path>
python validate.py orphans        <project-path>
python validate.py scope          <project-path>
python validate.py migrations     <project-path>
python validate.py ujt-coverage   <project-path>                       # opt-in, not in `all`
python validate.py vocab          <project-path> --repo <repo-path>    # opt-in, not in `all`
python validate.py all            <project-path>
```

Invoke `validate.py` with its absolute path (e.g. `python <skill-dir>/scripts/validate.py …`, where `<skill-dir>` is wherever the plugin or skill is installed). The script can be run from any working directory; only the `<project-path>` argument matters, since the design project lives in the user's Obsidian vault rather than next to the script.

| Subcommand | What it checks |
|---|---|
| `traceability` | Every `mvp`-tagged `[AC-NNN]` has at least one story covering it; every story's `**Traces to:**` line points at defined ACs; every `[AC-NNN]` references a defined `[V-NNN]` (via the `## Feature: [V-NNN]` heading in the AC file). |
| `ids` | No `[V-NNN]`, `[AC-NNN]`, `[S-NNN]`, `[D-NNN]`, or `[SCR-NNN]` is defined in more than one file. `T-NNN` and `M-NNN` (unbracketed) are tags, not checked for uniqueness. |
| `orphans` | Every bracketed `[XYZ-NNN]` reference anywhere in the project resolves to a real definition. |
| `scope` | Every `[AC-NNN]` definition carries a scope tag — `` `mvp` ``, `` `v2` ``, or `` `future` ``. Backtick-wrapped form is preferred; the bare form is only accepted at end-of-line (optionally inside parens) so titles like `### [AC-007] Future-proof X` don't get mis-tagged. |
| `migrations` | No file under `Issues/` or `Issues - */` still contains the literal `M_NEXT` placeholder. Design artifacts legitimately keep `M_NEXT` until Phase 8 claims a slot, so this check only fires on the post-substitution Issue surface. Soft-passes when no `Issues*/` directory exists. |
| `ujt-coverage` | Every `mvp`-tagged `[AC-NNN]` has at least one UJT in `User Journey Tests/` referencing it (frontmatter `traces_to:` or body `**Traces to:**` line). **Opt-in** — soft-passes when no UJTs exist. Not run by `all`. |
| `vocab` | Every Phase 8 issue body uses at least one term from `<repo>/CONTEXT.md`. **Opt-in** — soft-passes without `--repo` or without `CONTEXT.md`. Not run by `all`. Catches the failure mode where issue bodies drift from the project's domain glossary. |
| `all` | Runs traceability + ids + orphans + scope + migrations; prints each result and an overall verdict. Does **not** include `ujt-coverage` or `vocab`. |

### `migrations` — guards Phase 8 substitution

For projects with versioned database migrations, design files use the literal token `M_NEXT` as a placeholder for the migration slot. Phase 8 substitutes a concrete slot number (e.g. `M-042`) when generating Issue files. A stray `M_NEXT` in any Issue file means the substitution step was skipped — the implementer would commit a literal placeholder.

The check scans every file directly under `Issues/` or `Issues - */`. It soft-passes when no such directory exists (pre-Phase 8). Design artifacts outside the Issues surface are not scanned, since they keep `M_NEXT` legitimately until a slot is claimed.

### `ujt-coverage` — opt-in for UI-heavy projects

UJTs (User Journey Tests) prove ACs via observable behavior in the running app. See [user-journey-tests.md](../references/user-journey-tests.md) for the DSL and authoring conventions.

`ujt-coverage` is deliberately not part of `all` so headless projects (backend services, CLIs, pipelines) keep the same default validator output as UI projects. For UI-heavy projects, run it explicitly:

- Exit 0 if all MVP ACs are covered by at least one UJT.
- Exit 0 if `User Journey Tests/` does not exist or is empty (soft pass — the check is opt-in).
- Exit non-zero only when some UJTs exist but coverage is incomplete (or a UJT traces to a non-existent AC).

UJT files are discovered under `{project-path}/User Journey Tests/`. AC references are pulled from either:

- The frontmatter `traces_to:` list (inline `[AC-001, AC-002]` or block form with `-` items), or
- A body `**Traces to:** [AC-001], [AC-002]` line.

Add `ujt-coverage` to the Phase 7 review for UI projects; skip it for headless ones.

### `vocab` — opt-in for projects with a CONTEXT.md

The vocab check enforces the contract that Phase 8 issue bodies use the project's domain glossary. It expects a `CONTEXT.md` at the repo root (or wherever the user keeps the project repo) written in the format from `grill-with-docs/references/CONTEXT-FORMAT.md` — each defined term is a bold heading line `**TermName**:` followed by the definition.

The check is conservative: it flags only issues whose body has *zero* whole-word overlap with any glossary term, which is a strong signal of vocabulary drift without producing false positives on issues that legitimately discuss a niche subset of the domain.

- Pass `--repo <path>` pointing at the project repo root.
- Soft-passes if `--repo` is omitted, if `CONTEXT.md` doesn't exist, or if `CONTEXT.md` has no defined terms.
- Soft-passes if no `Issues*/` directory exists in the project (pre-Phase 8).

Run it after Phase 8 issue generation as a final gate before the implementer-agent flow picks up the issues.

### Exit codes

- `0` — PASS
- `>0` — number of failures. Phase 7 treats any non-zero exit as an automatic Blocker.

### When to run

- **Phase 2** completion: `traceability` and `scope` must PASS before the gate.
- **Phase 5** completion: `traceability` must PASS before the gate.
- **Phase 7** review: `all` runs first; failures = automatic Blockers.
- **After every rework** in the multi-pass cycle: `all` to catch propagation gaps.

### Definition vs reference

A *definition* line is a heading or list item that introduces an ID:

```markdown
### [AC-001] User logs in `mvp`
### **[AC-001]** User logs in `mvp`
- **[AC-001]** User logs in (`mvp`)
> [!note] [D-001] Local-First
```

A *reference* line mentions an ID after a label or in prose:

```markdown
## Feature: [V-001] Login           (back-reference)
**Traces to:** [AC-001], [AC-002]   (story → ACs)
- [SCR-013]'s addendum list ...     (body prose in a list)
```

The validator distinguishes by requiring the bracket to sit immediately after the heading/list/callout marker (optionally inside bold/italic) for it to count as a definition.

### Tolerated formatting variations

- Headings at any level (`#` through `######`)
- List items (`-` or `*`)
- Obsidian callouts with explicit type: `> [!note] [D-001] Title` counts; `> [D-001] is a continuation line` does not.
- IDs wrapped in `**bold**`, `__bold__`, `_italic_`, or `*italic*`
- Scope tags as backtick-wrapped (`` `mvp` ``, `` `v2` ``, `` `future` ``) — preferred — or bare at end-of-line (`### [AC-001] Title mvp` or `### [AC-001] Title (mvp)`). Bare scope words anywhere else on the heading line are ignored, so `### [AC-007] Future-proof X` is not mis-tagged as `future`.

### Canonical definition locations

To prevent body-text references in list-item form (e.g. `- [S-017] performance harness is bumped late...`) from being misread as definitions, each ID prefix has a canonical location glob. The defaults match the standard app-design layout:

| Prefix | Where definitions live |
|---|---|
| `V` | `Vision*.md` |
| `AC` | `Acceptance Criteria/**`, `Acceptance Criteria - */**` |
| `S` | `Stories/**`, `Stories - */**` |
| `SCR` | `Wireframes*.md`, `Wireframes/**`, `Wireframes - */**` |
| `D` | `Architecture*.md`, `Decisions/**`, `Decisions - */**` |

A line that *looks* like a definition in any other file is treated as a reference. Override the defaults by changing `DEFAULT_CANONICAL_DEF_LOCATIONS` at the top of `validate.py`.

### Reference-only files

Some files are not allowed to introduce *any* definitions, no matter the file name match — they're summaries, indexes, or dependency-list documents that mention IDs in heading/list form purely for reference. Defaults:

- `Issues*/**` and `Issues - */**` (Phase 8 issue files)
- `Design Review*.md` (review reports)
- `*Index*.md` and `**/00-*.md` (index documents, case-insensitive)
- `*Sweep*.md`, `Open Questions.md`, `*Rollout Plan*.md`, `Dependency Graph*.md`
- `Ideas/**` (non-canonical idea staging)

### Backtick literals exempt from orphan check

An ID whose every reference is wrapped in single backticks (`` `[S-110]` ``) is treated as a literal mention rather than a cross-link. This prevents Phase 5 notes like "new stories continue from `[S-110]`" from registering as orphans. As soon as the ID is used in a real link (`[S-110]` without backticks), the orphan check applies.

### Flags

```
--ignore GLOB                  Skip a file entirely. Repeatable.
--ref-only GLOB                Add a reference-only glob. Repeatable.
                               Adds to the defaults unless overridden.
--no-default-ref-only          Disable the built-in reference-only defaults.
--repo PATH                    Path to the project repo (where CONTEXT.md
                               lives). Used by the `vocab` subcommand.
```

Globs are matched case-insensitively against the path relative to `<project-path>`.

### Limitations

- The validator only reads markdown under the given path. It does not parse code, schemas, or external docs.
- It does not enforce sizing rules from Phase 5 (those are human judgment).
- It does not verify arithmetic in AC prose — that's the computed-expected-values check in Phase 7.
