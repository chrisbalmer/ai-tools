# Promotion Cycle & Scope Changes

This reference covers two related workflows:
1. **Promotion cycle** — Moving `v2` or `future` criteria into active development after MVP ships
2. **Mid-build scope change** — Handling new requirements discovered during implementation

Both use the same design infrastructure (IDs, traceability, Obsidian notes) but follow lighter-weight paths than the full 8-phase process.

---

## Reworking Existing Artifacts

Both flows below — and the multi-pass rework loop in Phase 7 — eventually require *editing* artifacts already in the project. A concept rename, a schema change, a corrected expected value, a renumbered migration: any of these can ripple through the project and miss artifacts that should be updated.

### Pre-edit audit

> [!important] Before any rework that touches a concept, list every artifact that mentions it
> Search the project directory for every reference to the concept (name, ID, value, file path) being changed. Build the list explicitly before editing. For each artifact, decide one of: *needs update*, *deliberately not updated (with reason)*, *not affected*. Then do the edits.

Concrete approach:
```bash
# In the project directory
grep -rn "OldConceptName" .
grep -rn "[AC-042]" .   # ID being renumbered or merged
grep -rn "2026-05-15" . # date being corrected
```

The audit takes minutes; the propagation Blocker it prevents costs an entire review pass.

### Post-rework validation

After every rework, run:

```bash
python {app-design-skill-path}/scripts/validate.py all {project-path}
```

`validate.py all` catches the structural propagation gaps a human pre-edit audit misses — orphan references to deleted IDs, ACs that now point at non-existent vision features, stories referencing dead ACs. Failures are automatic Blockers and need fixing before re-handing the package to a fresh verifier.

Phase 7's "Did the rework propagate?" check confirms both the pre-edit audit and validator were run.

---

## Migration Slot Allocation (`M_NEXT`)

For projects with versioned database migrations (Rails, GRDB, Django, Alembic, etc.), migration slots are a recurring source of merge-time drift. The convention:

> [!important] Claim migration slots at Phase 8, not earlier
> Design artifacts (Architecture.md, Acceptance Criteria/, Stories/) refer to migrations as `M_NEXT` rather than a concrete `M-042`. The concrete slot is assigned **at Phase 8 issue creation time**, after a fresh check of the actual current head in the codebase.

Why: a design that names `M-042` in Phases 2-7 may be obsolete by the time Phase 8 runs if any other branch has merged a migration in between. The branch that ships first wins the slot; the others rebase. By using `M_NEXT` until Phase 8, the design artifacts don't accumulate stale slot claims.

### Phase 8 substitution procedure

When generating an issue file that references a migration:

1. **Check the live head**: `ls Path/To/Migrations/M*.{ext} | sort -V | tail -3` (or the project's equivalent).
2. **Claim the next slot**: if head is `M041`, your slot is `M042`.
3. **Substitute** every `M_NEXT` reference across the package: the issue body, the AC, the architecture section, any pre-edit-audit-discovered mentions.
4. **Run** `python {app-design-skill-path}/scripts/validate.py all {project-path}` after substitution to catch any missed references (the `migrations` check will fail if any `M_NEXT` token is still in an Issue file).
5. **Lock the slot in the issue body** with the precheck instruction: "If a new migration has merged in the interim, use the next number after that and update every in-package reference in the same PR."

The precheck instruction handles the race where a Phase 8 file is created on Monday but the PR lands on Wednesday. The slot in the file is a *recommendation*, not a contract; the implementer re-checks at PR time.

Migration IDs are permanent once a migration is merged. If a migration needs to be reverted or rewritten, it gets a new `M-NNN`.

---

## Promotion Cycle

Use this after the MVP (or a previous release) is built and the user is ready to tackle the next batch of features. The full vision, architecture, and conventions already exist — this cycle focuses on what's new or changed.

### When to Trigger

- User says "let's start on v2" or "promote these features"
- User wants to add `v2` or `future` items to the active build
- User returns after shipping MVP and wants to expand

### Step 1: Retrospective Check

Before promoting anything, acknowledge that building the MVP probably taught the user things. Ask:

> "Before we promote v2 features, let's check: now that you've built and used the MVP, has anything changed? Any v2 features that turned out to be unnecessary? Any new ideas that weren't in the original vision? Any MVP features that need rework before we layer more on top?"

This step produces updates to existing documents:
- **Vision.md**: Add new features with the next available `[V-NNN]` IDs. Mark any removed features as `[DROPPED]` rather than deleting them (ID stability).
- **Existing AC notes**: Mark any obsolete criteria as `[DROPPED]` with a brief reason.

### Step 2: Promote & Revise Criteria

Review all `v2`-tagged (or `future`-tagged) acceptance criteria. For each one:

1. **Still relevant?** If not, mark `[DROPPED]` with reason.
2. **Still accurate?** Requirements evolve after real usage. Rewrite criteria that no longer match reality.
3. **Promote**: Change the scope tag from `v2` to `mvp` (or `future` to `v2` for the next cycle).
4. **New criteria needed?** If the retrospective surfaced new features, write fresh criteria with new `[AC-NNN]` IDs.

Update the MVP Scope Summary in the acceptance criteria notes.

> [!important] `mvp` is the active-cycle tag, not a shipped marker
> A promoted AC keeps the `mvp` tag for life — there is no `shipped` or `cycle:vN` distinction. The traceability check stays green across cycles because the `Stories/` directory is append-only: stories from earlier cycles continue to satisfy the "every MVP AC has a story" rule for ACs already built, and new stories for the freshly-promoted ACs are added alongside. To know which cycle actually built which AC, consult the corresponding `Design Review - vN.md`.

**Gate:** "Here are the promoted criteria for this cycle. Are they accurate, complete, and correctly scoped?"

### Step 3: Wireframe Delta

Only if the promoted criteria introduce new screens or significantly change existing ones.

- Add new screens with the next available `[SCR-NNN]` IDs
- Update existing screen wireframes if new elements are needed
- Update the navigation flow diagram
- Skip this step entirely if the promoted features are backend-only or fit within existing screens

**Gate:** "Do the updated wireframes cover the new features? Any new screens missing?"

### Step 4: Architecture Delta

The existing system is now the "current state." This step is lighter than Phase 4 but covers the same ground for what's changing:

1. **Document drift**: What changed during MVP implementation that diverged from the original architecture doc? Update Architecture.md to reflect reality, not the original plan.
2. **Schema changes**: New or modified entities for the promoted features. Add to the ER diagram.
3. **New components or APIs**: If the promoted features need new services, endpoints, or integrations, add them to the component map.
4. **Cross-cutting concerns revisit**: Check the checklist again. Promoted features may introduce new cross-cutting needs (e.g., v2 adds multi-user support → auth model changes, v2 adds offline mode → sync strategy needed).

**Gate:** "Does the updated architecture cover what we need for this cycle? Any cross-cutting concerns that now need attention?"

### Step 5: Stories, Dependencies, Review, Issues

Run Phases 5–8 as normal but scoped to the newly promoted criteria only. The existing build phases and issue numbers are preserved — new stories get the next available `[S-NNN]` IDs and new issues get matching numbers.

When building the dependency graph, include dependencies on existing (already-built) stories. These show up as "already completed" nodes in the graph — they're context, not work.

### Output

The promotion cycle doesn't create new top-level documents — it updates existing ones:
- Vision.md gets new features (or `[DROPPED]` markers)
- Acceptance Criteria notes get promoted tags and new criteria
- Wireframes.md gets new screens and updated flows
- Architecture.md gets delta updates and drift corrections
- New Stories notes get created under `Stories/`
- New Dependency Graph entries are added (or a new graph for the cycle)
- A new Design Review is produced for this cycle only
- New Issue files are created under `Issues/`

> [!tip] Cycle Naming
> To keep things organized across multiple promotion cycles, prefix the new Design Review and Dependency Graph with the cycle: `Design Review - v2.md`, `Dependency Graph - v2.md`. Stories and Issues don't need this — their IDs are globally unique.

---

## Mid-Build Scope Change

Use this when something is discovered during coding that requires new design work. This is not a bug fix or implementation detail — it's a genuinely new requirement or a realization that an existing design decision was wrong.

### When to Trigger

- A developer (or Claude Code) hits a case the design didn't anticipate
- The user tries the in-progress app and realizes something critical is missing
- An external dependency or constraint changes (API deprecation, library limitation, etc.)
- A story turns out to be impossible or impractical as designed

### Severity Assessment

Not all scope changes need the same treatment. Assess before acting:

**Minor — handle inline:**
- A story needs an extra field or validation rule not in the AC
- An edge case needs handling that fits within an existing story's scope
- A wireframe needs a small tweak (extra button, rearranged layout)

For minor changes: update the relevant design document directly, add a note to the affected issue, and continue. No formal cycle needed.

**Moderate — lightweight design pass:**
- A new story is needed that wasn't anticipated
- An existing story needs to be split or significantly reworked
- A new screen or major screen modification is required
- A cross-cutting concern that was deferred now turns out to be needed

For moderate changes: follow the abbreviated process below.

**Major — full promotion cycle:**
- An entire feature area was missed
- The architecture needs fundamental changes
- A core technical decision was wrong (e.g., wrong database choice)

For major changes: treat it as a promotion cycle (above), but entered mid-build rather than between releases.

### Abbreviated Process for Moderate Changes

1. **Document the change trigger**: What was discovered, why the existing design doesn't cover it. Write this as a callout in the affected design document.

2. **Write or revise acceptance criteria**: New criteria get the next available `[AC-NNN]` ID. Tag them as `mvp` (since they're needed now). Revised criteria keep their existing ID with a revision note.

3. **Update affected documents**: Wireframes, architecture, or cross-cutting concerns — only what's touched by this change.

4. **Write stories**: New stories get the next available `[S-NNN]` ID.

5. **Check dependencies**: Does this new work block or unblock anything in the current build plan? Update the dependency graph.

6. **Create issues**: Follow the Phase 8 format for the new stories.

7. **Gate**: Present the scope change to the user before adding it to the active build. Even if it seems urgent, the user should approve: "During implementation we discovered {X}. Here's what I think we need to add. Should we include this now or park it for later?"

### What NOT to Do

- Don't create new `[V-NNN]` vision features for mid-build discoveries. If it's truly a new feature, park it for the next promotion cycle. Mid-build changes should trace to existing vision features that were under-specified.
- Don't renumber or reorganize existing stories to "make room" for the new ones. IDs are permanent — new work gets new IDs at the end of the sequence.
- Don't skip the user gate. Mid-build scope creep is how projects derail. The user deciding "yes, we need this now" is different from the design skill unilaterally expanding scope.

### Output

Mid-build scope changes produce:
- Updated design documents (in-place edits, not new files)
- New story and issue files (following existing conventions)
- A scope change callout in the Design Review noting what was added and why

```markdown
> [!warning] Mid-Build Scope Change ({date})
> **Trigger:** {what was discovered}
> **Impact:** Added [S-NNN], [S-NNN]. Modified [AC-NNN].
> **Approved by user:** {date}
```
