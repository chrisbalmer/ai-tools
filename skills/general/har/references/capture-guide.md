# Capturing a useful HAR

Brief for the human who has the browser. The goal is a capture where each network request can be tied back to one deliberate UI action.

## Before recording

- Use a **throwaway or test object** (test indicator, sandbox incident). Every write in the capture is a real write on the tenant.
- Open dev tools **before** loading the page so the first requests (config, session bootstrap) are in the log.
- Network panel settings:
  - **Preserve log** on — navigation must not clear the capture.
  - Filter to **Fetch/XHR** (Chrome) / **XHR + Fetch** (Firefox) / **XHR/Fetch** (Safari) so assets stay out of the way while you work. The export still includes everything; the filter is only for your view.
  - **Disable cache** is optional; it doesn't affect API calls.

## While recording

- Perform **one action at a time**, pause a second or two between actions, and **write down the sequence** as you go — e.g.

  ```
  1. opened indicator 9cb4…
  2. edit → verdict Benign + Block → Save
  3. Enrich button
  4. edit → verdict Suspicious + unblock → "Save & enrich"
  ```

  The agent maps entries to actions by timestamp order; the list is what makes that mapping unambiguous.
- Prefer the **minimal** version of each action first (one field changed), then the compound version (several fields, or "save and X") if the UI offers one. Compound actions reveal flags like `enrichAfterSave`.
- If an action has an obvious *undo* (unblock, reopen), record it too — it shows the same call with the opposite value and proves the field is a toggle, not a one-way route.
- Do a **plain reload** of the object at the end so the capture ends with a clean `GET` of the final state.

## Exporting

| Browser | How |
|---|---|
| Chrome / Edge | Network panel → ⬇ **Export HAR…** (or right-click a request → *Save all as HAR with content*). Newer Chrome asks *with* or *without* sensitive data — choose **with**; the sanitizer removes it and "without" also strips bodies you need. |
| Firefox | Network panel → ⚙ → **Save All As HAR**. |
| Safari | Web Inspector → Network → **Export** (top-right) → `.har`. |

Save it to the project's gitignored scratch dir (`tmp/` or the project's captures dir) and tell the agent the path plus the action list. Don't paste the HAR contents into chat.

## What a good capture contains

- The `GET` of the object *before* the first write (so write-only keys can be diffed out).
- Each write, with its response.
- The `GET` after the last write.
- Anything the UI called that you didn't expect — leave it in; the agent filters.

## What to leave out or redo

- Logging in during the capture: the login exchange is pure secrets and adds nothing. Log in first, then start recording. (If the *login* flow is what's being captured, say so; the sanitizer redacts the credentials but the flow is a separate, HITL-only exercise.)
- Multiple tabs of the same app: cross-tab session polling muddies the timeline. One tab.
- Browser extensions that inject requests (password managers, ad blockers): disable for the session if they show up in the log.
