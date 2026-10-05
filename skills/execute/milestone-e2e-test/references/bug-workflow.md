# Bug Workflow

Steps for diagnosing, filing, fixing, and retesting a bug found during E2E testing.

For anything that isn't an obvious one-line fix (typo, missing CSS class, hardcoded URL), **route through [[diagnose]] discipline**: build a deterministic feedback loop, generate 3–5 ranked hypotheses before testing any of them, then write the regression test before the fix. Skipping diagnosis on a non-trivial bug is the failure mode this skill set exists to prevent — the "I'll just fix the symptom" reflex leaves the root cause in place.

For trivial bugs, the lightweight workflow below is sufficient. Use judgment: if the second attempt at the fix doesn't take, you're in `/diagnose` territory.

## 1. Diagnose

When a test fails, gather evidence from multiple sources before jumping to code:

### Browser-Side
```
read_console_messages(onlyErrors: true) → JavaScript errors
read_network_requests(urlPattern: "/api/") → failed API calls (4xx/5xx)
read_page → missing or unexpected DOM elements
screenshot → visual state at failure
```

### Server-Side
```bash
docker compose logs app --tail=50  # or however the app runs
```

Look for: panics, error-level logs, SQL errors, auth failures, validation errors.

### Source Code
Once you have an error message or failing endpoint, trace it:

1. Find the handler or component involved (Grep for the endpoint, error message, or component name)
2. Read the relevant code
3. Identify the root cause

**Common root causes:**
- Frontend/backend contract mismatch (query params, payload shape, limits)
- Missing configuration or environment variables
- Library defaults that don't match app expectations (e.g., dnd-kit sensors)
- CSS/layout issues hiding or misplacing elements
- Race conditions in async rendering
- Session or auth state not persisting across rebuilds

## 2. File a Gitea Issue

Create an issue via Gitea MCP (`issue_write`, method `create`):

- **Title:** `Bug: <concise description of what's broken>`
- **Milestone:** current milestone ID
- **Labels:** `priority:high` (or appropriate priority label ID)
- **Body:**

Keep each section to a sentence or two — paste only the relevant error lines, not whole logs. The issue is a record, not a report.

```markdown
## Description
<What was expected vs what happened — 1–2 sentences>

## Error
<The relevant error message / HTTP status / console lines only>

## Root Cause
<What in the code is causing this — 1–2 sentences>

## Fix
<What change resolves the bug — 1–2 sentences>

## Files Changed
- `path/to/file`: <what changed>
```

## 3. Fix the Code

Make the minimal change to resolve the bug. Principles:

- **Fix the root cause**, not the symptom
- **Don't refactor** surrounding code — scope the change to the bug
- **Don't add features** — if you notice something else while fixing, that's a separate issue
- **Match existing patterns** — follow the conventions in the codebase

## 4. Commit

Stage only the changed files (never `git add .`):

```bash
git add path/to/changed/file
git commit -m "$(cat <<'EOF'
Fix: <short description> (#<issue-number>)

<One-line explanation of root cause and fix>
EOF
)"
```

## 5. Push

```bash
git push origin <milestone-branch>
```

Push directly to the milestone branch — these are hotfixes during testing, not feature work.

## 6. Close the Issue

Via Gitea MCP (`issue_write`, method `update`, state `closed`).

## 7. Rebuild if Needed

Determine if a rebuild is required:

| Change Type | Rebuild Required? |
|-------------|-------------------|
| Go backend code | Yes (recompile + restart container) |
| Frontend JS/TS/CSS | Yes (Vite rebuild + restart container) |
| SQL migrations | Yes (restart to run migrations) |
| Config files (yaml, env) | Yes (restart container) |
| Static assets only | Maybe (depends on embed vs serve) |

If rebuild is needed:
1. Run the app startup command again
2. Wait for health check
3. Navigate to the app in Chrome
4. **User must re-authenticate** if the container was rebuilt (sessions are lost)
5. Tell the user to re-auth and wait for confirmation

## 8. Retest

After the fix is deployed:

1. Re-run the specific test that failed
2. Re-run any tests in the same category that could be affected
3. Spot-check one test from a different category to verify no regressions

Only mark the test as PASS after the fix is verified in the browser.

## Multiple Bugs in One Test

If a test reveals multiple distinct bugs:

1. Fix the first (most fundamental) bug
2. Retest — the other "bugs" may have been symptoms of the first
3. If additional bugs remain after the fix, repeat the workflow for each

Do not batch multiple unrelated fixes into one commit. Each bug gets its own issue and commit.
