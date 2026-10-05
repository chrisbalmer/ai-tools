# Per-Test Execution Workflow

Detailed steps for executing a single E2E test case within the milestone-e2e-test workflow.

## 1. Preconditions

Before executing a test:
- App is running and responding
- Browser tab is open and authenticated
- Network and console tracking are active

If any precondition fails, fix it before proceeding. Do not skip tests.

## 2. Navigate to Starting State

Get to the page or state required for the test:

```
navigate → URL or click → sidebar/nav link
wait → page load (1-2 seconds)
screenshot → verify starting state
```

Use `read_page` with `filter: interactive` to confirm expected elements exist before interacting.

## 3. Perform the Action

Execute the test action. Match the interaction to the element type:

| Element | Tool | Approach |
|---------|------|----------|
| Link / nav item | `computer` click by ref | Click the ref from `read_page` |
| Button | `computer` click by ref | Prefer ref over coordinates |
| Text input | `computer` click → type | Click to focus, then type |
| Form field | `form_input` by ref | Set value directly |
| Dropdown/select | `form_input` by ref | Set by value or text |
| Keyboard shortcut | `computer` key | e.g., `Escape`, `Return`, `cmd+k` |
| Drag-and-drop | `computer` left_click_drag | start_coordinate → coordinate |

**Prefer ref-based clicks over coordinate clicks.** Coordinates are fragile and shift with layout changes. Use `read_page(filter: interactive)` to get refs.

**After each action, wait 1-2 seconds** for the UI to respond before verifying.

## 4. Verify the Result

Check multiple signals to confirm the test passed:

### Visual Verification
```
screenshot → inspect the rendered state
zoom → inspect specific regions if needed
```

### Structural Verification
```
read_page → check that expected elements, text, or state changes are present
```

### API Verification
```
read_network_requests → confirm API calls returned expected status codes (200/201)
```

Watch for:
- 4xx/5xx responses (bugs)
- Missing API calls (action didn't trigger)
- Unexpected API calls (side effects)

### Error Verification
```
read_console_messages(onlyErrors: true) → should return no errors
```

Any console error during a test is a failure, even if the UI looks correct.

## 5. Record the Result

For each test, record:

- **Test name** — short descriptive name
- **Category** — navigation, CRUD, interactive, etc.
- **Result** — PASS or FAIL
- **Evidence** — what was checked (screenshot ID, network status, element presence)
- **Notes** — if FAIL, what went wrong; if PASS with caveats, note them

## 6. Clean Up State

If the test created data (tasks, areas, etc.), note it but do not delete it unless it interferes with subsequent tests. Test data helps verify list views, counts, and filters.

If the test changed navigation state, return to a known starting point before the next test.

## Interaction Pitfalls

Common issues when testing via Chrome MCP:

### dnd-kit / Drag Libraries
Click actions may be swallowed by drag-and-drop libraries. If clicking a draggable element doesn't trigger `onClick`:
- Check if the element has a PointerSensor with an `activationConstraint`
- A missing distance/delay constraint means all clicks become drags
- This is a real bug — file it

### Modals and Overlays
- Overlays may trap focus — use `Escape` to dismiss
- Elements behind overlays are not clickable
- After dismissing, re-read the page to get fresh refs

### Auth and Sessions
- Container rebuilds kill sessions — user must re-authenticate
- Always verify auth state after a rebuild by checking for the user menu or auth indicator
- If redirected to login, stop and ask user to re-auth

### Timing
- SPAs may render asynchronously — wait 1-2 seconds after navigation
- API mutations (POST/PUT/DELETE) may trigger refetches — wait before verifying
- Debounced inputs (search) need extra wait time (300-500ms after last keystroke)

### Stale Refs
- Page refs (`ref_1`, `ref_2`, etc.) become stale after any DOM change
- After navigation, form submission, modal open/close, or any state change: call `read_page` again to get fresh refs
- Never reuse refs across different page states
