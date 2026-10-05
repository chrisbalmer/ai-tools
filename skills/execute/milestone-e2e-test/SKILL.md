---
name: milestone-e2e-test
description: "End-to-end browser testing for milestone validation before merge to main. Uses Chrome MCP to visually verify features, find bugs, file issues, fix them, and retest until the milestone is clean. Fits after milestone-builder and before final human review and merge. MANDATORY TRIGGERS: e2e test, end to end test, test milestone, validate milestone, browser test, milestone testing, smoke test milestone, acceptance test milestone, verify milestone, milestone QA, QA milestone, final testing."
---

# Milestone E2E Test

Validate a milestone branch via browser-based end-to-end testing. Find bugs, file issues, fix them, commit, and retest until the milestone is clean for human review.

## Philosophy

- **Test what the user sees** — verify via browser, not just API or unit tests
- **Fix forward** — bugs found during testing get issues, fixes, and commits on the milestone branch
- **Each bug is atomic** — one issue, one commit, one fix
- **Retest after fixes** — rebuild, re-auth, re-run affected tests after any code change
- **Leave it clean** — when testing passes, the milestone is ready for human review and merge

## Pipeline Position

```
app-design → milestone-builder → milestone-e2e-test → human review → merge to main
```

This skill picks up after milestone-builder has merged all issue PRs into the milestone branch. It validates the integrated result before the final PR to main is reviewed.

## Startup

When triggered, gather:

1. **Repository** — check `git remote -v` for owner/repo
2. **Current branch** — confirm we're on the milestone branch (e.g., `milestone-8-polish-completion`)
3. **Milestone** — identify the milestone from the branch name or ask the user
4. **App startup command** — ask the user how to start the app (e.g., `docker compose up --build`, `go run ./cmd/server`, etc.)
5. **App URL** — ask or infer the local URL (default: `http://localhost:8080`)
6. **Auth required?** — ask if the user needs to authenticate manually before testing begins

Then read the project's `CLAUDE.md` for tech stack, conventions, and project structure.

## Workflow

### 1. Start the App

Run the user-provided startup command in the background. Wait for the health endpoint (if known) or poll the app URL until it responds.

### 2. Open Browser

Use Chrome MCP to open the app:

1. `tabs_context_mcp` — get current browser state
2. `tabs_create_mcp` — create a new tab
3. `navigate` — go to the app URL

If auth is required, tell the user to sign in and wait for confirmation.

### 3. Build Test Plan

Read the milestone's scope to build a test plan. Sources (in priority order):

1. **Gitea milestone issues** — fetch closed issues for the milestone via MCP. Each issue's acceptance criteria are test cases.
2. **CLAUDE.md** — project conventions, key features, known views
3. **Visual inspection** — read the page to discover navigation, views, and interactive elements

Organize tests by area:

- **Navigation** — sidebar, routing, area switching
- **Core views** — each major page (board, list, inbox, settings, etc.)
- **CRUD operations** — create, read, update, delete for primary entities
- **Interactive features** — drag-and-drop, modals, overlays, search, filters
- **Auth & session** — user display, sign out, session persistence
- **Error states** — empty states, invalid input, network failures

Present the test plan to the user for approval before executing.

### 4. Execute Tests

For each test, follow the test execution workflow in [references/test-execution.md](references/test-execution.md).

Summary for each test:

1. Navigate to the relevant page/state
2. Take a screenshot before the action
3. Perform the action (click, type, submit, etc.)
4. Wait for response/render
5. Take a screenshot after the action
6. Verify the expected result via screenshot + accessibility tree + network requests
7. Record PASS or FAIL with evidence

**Key testing tools:**
- `read_page` — verify element presence and structure
- `computer` (screenshot) — visual verification
- `computer` (click/type/key) — interact with the app
- `read_network_requests` — verify API calls succeed (watch for 4xx/5xx)
- `read_console_messages` — catch JavaScript errors
- `form_input` — fill form fields

**Important:** Enable network and console tracking early (call `read_network_requests` and `read_console_messages` at least once before testing begins, so tracking is active).

### 4a. Comp Diff Pass

If the project has a Design bundle with Comps, run a per-screen visual diff after functional tests pass:

1. **Collect Comp file paths** — read the milestone's issues for `## Comp Reference` sections; build a list of every `[SCR-NNN]` → Comp screenshot path in the Design bundle
2. **For each screen:**
   - Navigate to the screen in the running app
   - Screenshot the rendered state (`computer` screenshot)
   - `Read` the Comp screenshot from the Design bundle (Claude sees images directly — no browser tab needed)
   - Compare: layout, spacing, color, typography, content placement, empty/loaded/error states
   - Record PASS or list specific discrepancies (e.g., "sidebar width 280px in app vs. 320px in Comp", "missing empty-state illustration")
3. **Report Comp diff results** alongside the functional test results in step 6's summary table — add a `Comp diff` category row

Comp discrepancies are bugs. File and fix them through the same bug workflow (step 5). The Comp is the visual source of truth; "it looks fine to me" is not a pass — the diff must match.

Skip this step if no Comps exist (backend-only project or Design bundle was text-only).

### 5. Handle Failures

When a test fails, follow the bug workflow in [references/bug-workflow.md](references/bug-workflow.md).

Summary:

1. **Diagnose** — for a trivial failure (obvious one-line fix: typo, missing CSS class, hardcoded URL), check console errors, network responses, server logs, and source code directly. For anything non-trivial — unclear root cause, intermittent, or spanning modules — route through [[diagnose]] first (feedback loop, ranked hypotheses, regression test), per the routing rule at the top of the bug workflow. If a second fix attempt doesn't take, you're in `/diagnose` territory.
2. **File a Gitea issue** — with description, error, root cause, and fix (a sentence or two per field). Add to the current milestone with `priority:high`.
3. **Fix the code** — make the minimal change to resolve the bug
4. **Commit** — `Fix: <description> (#<issue-number>)`
5. **Push** — to the milestone branch
6. **Close the issue** — via Gitea MCP
7. **Rebuild if needed** — if the fix requires a rebuild (backend/Docker changes), rebuild and re-auth
8. **Retest** — re-run the failed test and any related tests

### 6. Report Results

After all tests pass (or after resolving all found bugs), present a summary:

```markdown
## E2E Test Results — Milestone <N>

### Test Summary
| Category | Tests | Pass | Fail | Fixed |
|----------|-------|------|------|-------|
| Navigation | X | X | 0 | 0 |
| Core views | X | X | 0 | Y |
| CRUD | X | X | 0 | 0 |
| Comp diff | X | X | 0 | Y |
| ...        | ... | ... | ... | ... |

### Bugs Found and Fixed
| Issue | Title | Commit |
|-------|-------|--------|
| #NN | Bug description | abc1234 |

### Bugs Found — Not Fixed (if any)
| Issue | Title | Reason |
|-------|-------|--------|
| #NN | Description | Needs user input / out of scope |

### Remaining Concerns
[Any observations, edge cases not tested, or recommendations]

### Verdict
[READY FOR REVIEW | NEEDS ATTENTION]
```

### 7. Milestone Handoff

When all tests pass:

1. Confirm the milestone branch is pushed with all fixes
2. Check if a PR from milestone branch → main already exists (it should from milestone-builder)
3. If not, create one
4. Report the PR link to the user for final human review

## Resuming

If a conversation ends mid-testing:

1. Check `git log` on the milestone branch for recent fix commits
2. Ask the user which tests have already passed
3. Re-start the app and browser
4. Continue from where testing left off

## When to Check In

- **Before executing tests** — present the test plan for approval
- **After finding a bug** — brief note before diving into the fix
- **After fixing a bug that requires rebuild** — user may need to re-auth
- **On test completion** — full results report
- **If stuck** — test requires manual interaction, app won't start, auth issues

Do NOT check in after every individual passing test. Report results in batches.

## References

| Reference | When to Read |
|-----------|-------------|
| [references/test-execution.md](references/test-execution.md) | Before running the first test — detailed per-test steps |
| [references/bug-workflow.md](references/bug-workflow.md) | When a test fails — diagnosis through fix and retest |
