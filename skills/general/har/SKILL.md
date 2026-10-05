---
name: har
description: "Process browser HAR network captures safely and repeatably: sanitize secrets and PII with a stdlib script, verify the redaction, read the capture through targeted digests instead of dumping it into the conversation, find the real endpoint/body a web UI uses for an action, diff a GET body against a POST body to isolate write-only keys, extract JSON bodies as test fixtures, and record the findings in the project's observed-API doc. MANDATORY TRIGGERS: here's a HAR, sanitize this HAR, redact the HAR, I exported a HAR from dev tools, network capture, what endpoint does the UI actually call, capture the real API call, extract a fixture from the HAR, the inferred endpoint returned 404/405, prep the HAR for reading. Also use proactively whenever a .har file appears in the working tree or an attachment before opening it. Do NOT use for writing the API client itself (that's the project's own conventions) or for generic log analysis."
---

# HAR capture processing

A **HAR** (HTTP Archive) is a browser dev-tools export of every request on a page: URLs, headers, cookies, bodies. It is the ground truth for "what does the web UI actually send" — and it is radioactive until sanitized: session cookies, CSRF tokens, bearer tokens, the tenant's hostname, real user emails, and tenant content are all in there verbatim.

This skill is the standard path from *raw export* to *documented endpoint + fixture*. Two stdlib scripts ship with it:

| Script | Job |
|---|---|
| `scripts/sanitize-har.py` | Raw HAR → sanitized HAR. Redacts secret headers/cookies/JSON keys and emails, optionally replaces your own domain (`--domain`), drops static assets. |
| `scripts/har-digest.py` | Read a sanitized HAR in small views: `list`, `show`, `keys`, `diff`, `extract`, `grep`. |

Both are in this skill's `scripts/` directory; call them by absolute path from the skill location (they are not installed on `PATH`).

## Rules that never bend

1. **Never `Read`, `cat`, or `grep` a raw HAR.** The transcript is durable context; a cookie printed once is leaked. All raw-file contact goes through `sanitize-har.py`, whose only output is the redaction summary.
2. **Never commit a raw HAR.** Keep it in a gitignored scratch dir (`tmp/` or `handoff/captures/`); check `.gitignore` covers it before the file lands.
3. **Sanitized ≠ public.** Indicator values, incident titles, hostnames of internal assets, and free-text content survive sanitization. Review the digest before attaching a sanitized HAR to an issue, and use `--replace` for anything tenant-specific.
4. **The capture wins.** When a HAR contradicts an inferred endpoint, a doc, or a comment in code, the HAR is right. Update the doc; don't rationalize the guess.

## Step 1 — Get the capture (or brief the human)

If the human has not yet recorded the HAR, load **`references/capture-guide.md`** and give them the short checklist: filter to Fetch/XHR, preserve log, perform *one* action at a time and say what each one was, export as HAR, and drop the file in the scratch dir. Ask for the **sequence of actions they performed** — you need it to map entries to intent (see Step 4).

## Step 2 — Sanitize

```sh
python3 <skill>/scripts/sanitize-har.py <raw>.har --list                 # preview kept requests, writes nothing
python3 <skill>/scripts/sanitize-har.py <raw>.har \
    --domain <your-domain> --replace '<username>=user1' \
    -o <scratch>/<topic>.sanitized.har
```

What it does by default: redacts `Cookie`/`Set-Cookie`/`Authorization`/CSRF+XSRF headers and the XSOAR-style `x-xdr-*` signing headers; redacts every cookie entry and any query param or JSON key whose name looks like a credential (`password`, `token`, `apiKey`, `session`, `csrf`, `nonce`, `signature`, …); replaces every email with `default-admin@example.com`; scrubs long opaque tokens (JWTs, ≥40-char hex) in free text; base64-decodes JSON bodies so they're readable; drops HTML/JS/CSS/image/font entries; strips Chrome's `_initiator` stacks; refuses to overwrite its input.

Flags you'll actually use: `--domain <your-domain>` (no default — domain replacement is off unless you pass it; pass it whenever the capture is from your own or your employer's host, so it becomes `example.com`), `--replace OLD=NEW` (repeatable — usernames, hostnames, project codenames), `--only-path /api/` (keep just one API prefix), `--keep-static`, `--no-opaque-scrub`.

## Step 3 — Verify the redaction

Before reading anything else, prove the sanitizer did its job on the **sanitized** file:

```sh
grep -c '<your-domain>' <sanitized>.har         # expect 0 when --domain was passed
grep -o '<REDACTED>' <sanitized>.har | wc -l    # expect > 0 if the capture had auth headers
```

Compare against the sanitizer's summary (`header:cookie`, `header:x-csrf-token`, `email`, `domain` counts). A zero where you expected hits means the capture used a header name the script doesn't know — add it to `SECRET_HEADERS` in the script (and commit that) rather than working around it.

## Step 4 — Read it in digests, not dumps

Work on the sanitized file only, with `har-digest.py`. Entry indexes are stable across all subcommands.

```sh
D="python3 <skill>/scripts/har-digest.py <sanitized>.har"
$D list --api                        # API traffic only; static + heartbeat chatter hidden
$D list --api --method POST          # the writes
$D keys 9                            # top-level keys + types of request and response bodies
$D diff 0 9 --side cross             # entry 0's GET response vs entry 9's POST request → the write-only keys
$D show 9 --depth 1 --headers        # skim bodies one level deep, plus the interesting headers
$D grep 'enrich' --api               # which entries mention a term (url or body)
```

Map entries to the human's action sequence by timestamp order and URL. Typical shape for a "what does the UI do when I click X" question:

- **Full-object read-modify-write**: the UI `GET`s an object, then `POST`s the *entire* object back plus a few write-only keys. `diff <get> <post> --side cross` isolates exactly those keys — that list *is* the API contract.
- **Script/command execution** instead of a REST write: look for `execute`, `run`, `script`, `command` in the path and a `scriptId`/`command` in the body.
- **Side channels**: session-message polling, websockets, notification banners. `list --api` hides the common ones; ignore the rest unless the answer isn't in the direct calls.
- **Server-written derived data**: compare the response of a write with the preceding GET (`diff <get> <post> --side resp`) — appended history/audit entries, bumped `version`/`modified`, server-rewritten timestamps.

Note what you *didn't* observe. A 405 on the inferred path plus a captured alternative does not prove the alternative accepts a minimal body, rejects a stale version, or honours a client-supplied attribution field. List those as open questions rather than implying they're settled.

## Step 5 — Record the findings

The capture is only useful once it's written down where the next agent will look.

1. **Observed-API doc** — the project's contract doc (e.g. `docs/api/<platform>-observed.md`). Add or correct a section with: method + path, the write-only keys as a table (key, type, meaning), a trimmed request example, the response shape, the derived data the server wrote, and an **"untested — verify before relying on it"** list. Strike through the wrong inference and say what it returned (`405`). Update the endpoint quick-reference table if there is one.
2. **Fixture** — `$D extract <n> --side resp -o docs/api/<topic>-sample.json` (and `--side req` when the request body *is* the contract). Mirror into the test bundle if the project's testing ADR says fixtures are seeded from `docs/api/`. Bundle request+response+related calls into one file when they only make sense together; add a `_comment` key naming the capture date and issue.
3. **Tracker** — post the endpoint table, the mapping bugs the capture exposed, and the fix scope on the originating Issue (see [[triage]] for the Agent brief shape if the Issue is about to go `ready-for-agent`). Point at the doc section and fixture by path.
4. **Code comments** — if the codebase marks inferred endpoints (e.g. an `R-2` / `TODO verify` convention), remove the marker only for the calls the capture actually exercised. Unexercised siblings stay marked.

## Step 6 — Hygiene

- Sanitized HAR stays in the scratch dir; attach to the Issue by hand if wanted. Commit the **fixture and doc**, not the HAR, unless the project already keeps sanitized captures in-repo.
- If a redaction gap was found (new header name, new secret key shape), fix the script in this skill and note it in the commit — the next capture should not need the same manual patch.
- Delete the raw HAR when the fixture and doc are merged; it has no further value and only risk.

## When not to use this skill

- The question is answerable from the vendor's public API docs or an existing observed-API section — read that first; only capture when the docs are silent or wrong.
- The traffic is a mobile app or CLI, not a browser: HAR export isn't available; use a proxy capture (mitmproxy/Charles) and convert to HAR, then continue at Step 2.
- You need to *write* the client code: that's the project's own conventions (adapter layout, DTOs, tests). This skill ends at "documented contract + fixture".
