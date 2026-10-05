# User Journey Tests (UJTs)

## Purpose — ACs vs UJTs

Acceptance Criteria are *behavior contracts*: "after deleting a book, it must not appear on the next dashboard load." They state what must be true, in any order, without prescribing how a user gets there.

User Journey Tests are *journey contracts*: "open the app, tap the book row, swipe left, tap Delete, confirm — the row disappears and the database row count drops by one." They prescribe a walk through the running app and the observations that prove the journey worked.

Both are needed. ACs are the spec; UJTs are the demonstration. An AC without a UJT is unproven in the real product. A UJT without an AC is an unscoped behavior — the AC is missing.

A UJT is something a person (or an automated runner) could *follow*. If you can't write it as a series of taps, types, and observations, the story it traces from is probably too abstract — that's the forcing function.

## The DSL — four primitives

Every line in the body of a UJT is one of four primitives. The vocabulary is deliberately small — UJTs read end-to-end like a script, not a test framework.

- **`STEP: <action>`** — a single user action: tap, swipe, navigate, scroll, long-press, dismiss. One verb, one target. If the action requires data entry, prefer a separate `INPUT:` line on the next line.
- **`EXPECT: <observable UI state>`** — an assertion about what the user can *see* on screen right now: a label, a button state, a row count, a sheet that is presented, a modal that has been dismissed. Must be observable from the UI alone.
- **`INPUT: field=value, field=value`** — form data entry. Comma-separated `field=value` pairs scoped to the screen the user is currently on. Use the visible label or the accessibility identifier of the field, whichever is more stable.
- **`STATE: <data-layer assertion>`** — an assertion that is *not* visible in the UI but must hold: a row count in SQLite, a setting written to UserDefaults, a file present in the app's container, a Keychain entry created. STATE is the escape hatch for things only the data layer can confirm; reach for EXPECT first.

Steps are numbered (`1.`, `2.`, …) and primitives are interleaved underneath the step they belong to. The numbering is for human-readable structure only — it has no meaning to the runner.

## File structure

UJTs live in `{ProjectName}/User Journey Tests/`, one file per journey (or a tight cluster of related canonical + variant journeys). File names mirror the journey name: `Add Book.md`, `Delete Book.md`, `Log Reading Session.md`.

```markdown
---
tags:
  - {project-tag}
  - user-journey
  - walkthrough
  - ujt
created: {YYYY-MM-DD}
traces_to: [V-002, AC-007, AC-008, S-014, T-021]
---

## [UJT-007] Add Book — happy path

**Persona:** First-time user with one book to log
**Preconditions:** App freshly installed, no books saved
**Traces to:** [AC-007], [AC-008], [S-014]

### Setup
- Reset simulator state (Settings → Erase All Content)
- Launch app from springboard
- Dismiss onboarding sheet if present

### Journey

1. STEP: Tap the "+ Add Book" button on the Dashboard
   EXPECT: The Add Book sheet is presented
   EXPECT: The "Title" field has focus and the keyboard is visible

2. STEP: Enter book details
   INPUT: Title=Dune, Author=Frank Herbert, Started=2026-03-15
   EXPECT: The "Save" button transitions from disabled to enabled

3. STEP: Tap "Save"
   EXPECT: The Add Book sheet is dismissed
   EXPECT: The Dashboard shows one row titled "Dune"
   EXPECT: The Dashboard subtitle reads "1 book"
   STATE: The `books` table contains exactly one row with title="Dune"

### Cleanup
- Delete the created book row (long-press → Delete) to leave the state clean for the next run

### Traces
- [AC-007] "Adding a book persists across launches" — STATE assertion in step 3 proves persistence
- [AC-008] "Dashboard count reflects current books" — EXPECT in step 3
- [S-014] "Add Book sheet"

### Variants
- [[Add Book#UJT-007-a — cancel mid-entry]]
- [[Add Book#UJT-007-b — validation: empty title]]
- [[Add Book#UJT-007-c — duplicate name]]

---

## [UJT-007-a] Add Book — cancel mid-entry

**Traces to:** [AC-007]

1. STEP: Tap "+ Add Book"
   EXPECT: Sheet presented

2. STEP: Enter partial data
   INPUT: Title=Du

3. STEP: Tap "Cancel"
   EXPECT: Sheet is dismissed
   EXPECT: Dashboard subtitle still reads "0 books"
   STATE: The `books` table is empty
```

Variants live in the same file as their canonical journey, separated by `---`. They reuse the parent's Setup/Cleanup unless they need to override.

## Execution modes

Two concrete modes today, one aspirational.

### Manual smoke test (concrete)

Anyone — the author, a teammate, the user — can pull up the markdown on a second screen and walk the document on a simulator or device, line by line. STEP/INPUT lines are things they *do*; EXPECT/STATE lines are things they *verify*. Failures get flagged inline with a `// FAIL:` comment on the offending line and reported back. This is the baseline — every UJT must be walkable this way.

### Automated via XCUITest (concrete)

An implementing agent translates the four primitives into Swift XCUITest:

| Primitive | Swift XCUITest equivalent |
|---|---|
| `STEP: Tap "X"` | `app.buttons["X"].tap()` |
| `STEP: Swipe left on row "Y"` | `app.cells["Y"].swipeLeft()` |
| `INPUT: field=value` | `app.textFields["field"].tap(); app.textFields["field"].typeText("value")` |
| `EXPECT: The X label reads "Y"` | `XCTAssertEqual(app.staticTexts["X"].label, "Y")` |
| `STATE: row count == N` | Test helper that opens a sqlite handle to the app group's DB and asserts |

The translation lives in `{ProjectRoot}/UJTRunnerTests/` (or the equivalent test target). Each UJT becomes one `func test_UJT_007_addBook_happyPath()`. Run via `xcodebuild test -scheme UJTRunner -destination 'platform=iOS Simulator,name=iPhone 15'`. On failure, the agent iterates: reads the test output, inspects which EXPECT/STATE failed, fixes the underlying code, re-runs.

STATE assertions usually need a small test-only helper (a `TestStateInspector` that the runner exposes via the app group) — design that helper once in Phase 4 and reuse it across UJTs.

### Interactive simulator MCP (aspirational)

If an interactive simulator MCP server ever lands in the registry, an agent could drive the simulator directly — interpreting STEP/EXPECT lines without the Swift translation step. That would shorten the loop and avoid maintaining two artifacts (the UJT and the generated XCUITest). For now, the XCUITest path is the only fully-automated option.

## Variants pattern

Every canonical UJT (`UJT-NNN`) should have at least the obvious variants spelled out:

- **`-a`** — user cancels mid-flow (back button, swipe-down on sheet, hardware back)
- **`-b`** — validation error (empty required field, invalid format)
- **`-c`** — edge: duplicate, max length, smallest/largest valid value
- **`-d`+** — domain-specific edges (offline, low storage, permission denied)

A variant inherits the parent's setup and cleanup. If a variant covers a different AC than the parent, list both ACs in its `Traces to:`. Variants are how UJTs exercise the *edge* ACs that the happy path doesn't touch — they're not optional embellishment, they're the bulk of the coverage.

Don't write variants the AC doesn't motivate. If there's no AC for "cancel mid-entry leaves no partial row," either write that AC or skip the variant — the UJT is proving an AC, not improvising one.

## Traceability rules

- **Every UJT traces to ≥1 AC and ≥1 story.** Listed in the frontmatter `traces_to:` and repeated in the body `**Traces to:**` line for human readability. If a UJT can't point at an AC, the AC is missing — write it.
- **Every MVP AC *should* have at least one UJT covering it.** This is a `should`, not a `must` — some ACs are headless (backend, CLI) and have no journey. The `ujt-coverage` validator surfaces uncovered MVP ACs; treat them as work to do, not as automatic Blockers.
- **Edge-case ACs are proven by variants.** "Adding a book fails gracefully when title is empty" is proven by `UJT-007-b`, not `UJT-007`. The variant's `traces_to:` is what makes the coverage real.
- **Stories list UJTs in their done-when.** A story's done-when reads "UJT-007 and UJT-007-a through -c pass on the simulator." That's the definition of done. The UJT *is* the done-when, in journey form.
- **AC frontmatter gets `proven_by: [UJT-NNN]` where applicable.** Optional but useful for spot-checking from the AC side without grepping the UJT folder.

## When NOT to use UJTs

UJTs are journeys *through a user interface*. Skip them for:

- Pure backend services with no UI — the API tests are already journey-shaped (request → response → state).
- CLI tools — the shell session itself is the journey; document expected output in the AC.
- Headless data pipelines, cron jobs, migration scripts.
- Libraries (the consumer's tests are the journey).

For these, the AC's "How we prove it" section is sufficient; don't invent UJTs to satisfy a convention. The `ujt-coverage` check is opt-in for exactly this reason — projects with no UJTs soft-pass.

## Authoring guidance

**Write UJTs during Phase 5, alongside the stories they prove.** Don't wait for Phase 7; by then the cost of discovering "this story can't actually be journey-tested" is high.

The flow inside Phase 5 for each story:

1. Write the story (title, traces-to, description).
2. Sketch the happy-path UJT in the same sitting. If you can't, the story is too abstract — split it or add detail to the architecture first.
3. List the obvious variants (`-a` cancel, `-b` validation, `-c` edge).
4. Fill in the story's "Done when" by referencing the UJT IDs: *"`UJT-007` and `UJT-007-a` through `-c` pass on the simulator."*

**UJTs are a forcing function.** The act of writing them surfaces gaps:

- Can't name the button the user taps? → The wireframe is incomplete.
- Can't write the EXPECT after the tap? → The behavior isn't specified yet.
- The STATE assertion needs a database helper that doesn't exist? → New story for the helper, traced from the same AC.
- The journey has 14 steps? → The story is too big; split it.

**Don't over-script.** A UJT is a script for *one user, one device, one run*. Don't try to encode multi-user flows, concurrency, or system-level chaos in the DSL — those belong in dedicated test suites, not UJTs.

**Keep STATE assertions rare.** Every STATE you write is a test-only helper you (or the agent) will have to build. Reach for EXPECT first; only drop to STATE when the data is genuinely invisible to the UI and the AC depends on it.

**Re-use language across UJTs.** "Tap the Save button" should appear verbatim everywhere a Save button is tapped. Consistency makes the XCUITest translation predictable and the manual walk less surprising.
