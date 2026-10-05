---
name: review
description: "Spec-adherence review of a PR or branch against its tracked issue, CONTEXT.md, ADRs, and any referenced Comps — the Reviewer role's procedure in the ship-issue and milestone-builder flows. The review-prep Utility agent (cheapest tier, see MODELS.md) assembles a Review packet (diff on disk, changed-file table, new identifiers checked against CONTEXT.md, ADR hits, tests added, migration presence, PR hygiene, optional headless screenshots); the Reviewer then reads the diff once, runs the Visual diff gate when a Comp Reference exists, and returns a fixed-shape report ending in a verdict: line the Main thread keys on. MANDATORY TRIGGERS: review PR #N, review this PR, review the branch, run the Reviewer on, spec review, review against the issue, review against the Comp, does this PR match the spec, is this ready to merge. Also the skill a Reviewer subagent invokes from a ship-issue or milestone-builder Stage 3 brief. Do NOT use for a generic diff review with no tracked issue (use /code-review), for architecture audits (/improve-codebase-architecture), or for whole-milestone browser QA (/milestone-e2e-test)."
---

# Review

The Reviewer's job is judgment: does the diff do what the issue says, is it correct, is it tested, does it use the glossary's vocabulary, does the rendered screen match the Comp. Everything *around* that judgment — fetching the diff, listing the changed files, grepping ADRs for the touched area, pulling new identifiers out of the hunks, taking screenshots — is mechanical, and on the strongest model it is pure waste. This skill splits the two: a **Review packet** assembled by the `review-prep` Utility agent (cheapest tier, see `MODELS.md`), then a Reviewer that consumes the packet and spends its context only on the diff and the verdict.

The report ends in a `verdict:` line. `ship-issue` Stage 4 and `milestone-builder` Stage 4 key on that line, so its shape is a contract — don't improvise it.

## Two entry modes

**Main-thread mode** — the user asked for a review (`/review 42`, "review PR #42", "is #42 ready to merge") or a ship-issue / milestone-builder run reached Stage 3. The Main thread does Steps 1–2, spawns a Reviewer for Steps 3–6, then hands the report to whatever comes next (Stage 4, or the user). The Main thread never reads the diff itself: that is exactly the bulky content the Reviewer exists to keep out of orchestrator context.

**Reviewer mode** — this skill was invoked inside a Reviewer subagent from a brief. The brief carries the packet path and the spec context; skip to Step 3. If the brief has no packet path, do Step 1 yourself (the `Agent` tool is usually unavailable to a subagent, so run the packet commands inline — they are listed in the plugin's `agents/review-prep.md`) and continue.

## Inputs

From the caller (or gathered in Step 1 when invoked standalone):

- **Target** — PR number (preferred), or a branch name, or a worktree path. Plus the **base branch** (`main`, or the Milestone branch).
- **Issue body** and any addenda / agent brief comments. Standalone: delegate to the `tracker-read` Utility agent with `full` scope; do not paste raw issue JSON.
- **`CONTEXT.md`** and the **ADRs that touch the area** — the packet names the ADR files; the caller pastes their content or the Reviewer `Read`s only those files.
- **Implementer's flagged judgment calls** — verbatim from the Implementer's report-back. Each one is a specific thing the Reviewer must rule on.
- **Points to scrutinize** — subtle spec sections (matrix tables, formula tie-breaks, sentinel error contracts), cross-cutting concerns, UJT-translated tests.
- **Visual diff inputs** — only when the issue has a `## Comp Reference`: the running app URL (the Main thread starts the app in the Implementer's preserved worktree before this skill runs) and the Comp screenshot paths from the issue.

## Step 1 — Assemble the Review packet (Main-thread mode)

Spawn the `review-prep` Utility agent (`subagent_type: "ai-tools:review-prep"`, `run_in_background: false` — the Reviewer brief depends on its output):

```
Brief for review-prep:
- repo: <owner>/<repo>  (Gitea)   base: <base branch>
- target: PR #<N>  (or branch <name> / worktree <path>)
- scratch dir: /tmp/review-<repo>-<N>
- CONTEXT.md path: <repo>/CONTEXT.md   ADR dir: <repo>/docs/adr/
- screenshots (only if Comp Reference): app URL <url>; pages: <route → name> for each screen the PR touches
- word budget: 300
```

Escalation applies per `agents/README.md`: on `confidence: partial` or `not-found`, re-spawn the same brief once on the Escalation tier named in `MODELS.md`, quoting what the first attempt already checked. If the retry also fails, run the packet commands inline on the Main thread — but keep the diff itself out of Main-thread context (write it to the scratch dir, don't `cat` it).

The packet digest is short enough for the Main thread to keep: its file table is also the Main thread's early warning for shared-file conflicts across parallel PRs (compare it with the other in-flight packets), missing `Resolves #N`, and PR-body footers the repo doesn't want.

## Step 2 — Spawn the Reviewer (Main-thread mode)

One Reviewer, read-only, no worktree, on the Reviewer model from `MODELS.md`, `run_in_background: true`. The brief is the input list above, plus:

- The packet path and the packet digest (paste it — it's small).
- "Invoke the `ai-tools:review` skill via the `Skill` tool with `PR #<N>, base <branch>, packet <path>`. If the `Skill` tool can't resolve it, follow the report shape below manually."
- Token discipline for the Reviewer, stated explicitly: *do not* fetch the PR via MCP (the diff is in the packet); *do not* re-read `CONTEXT.md`, the issue body, or ADRs pasted in the brief; read implementing files only in ranges around the hunks that need context, never whole files unless the file is new in this PR.
- The report shape (Step 6), verbatim, with the word cap.
- Posting policy: **do not post anything to the tracker**. The report comes back to the Main thread; the Main thread decides what to act on. If the Reviewer posts anyway, the `posted:` line must say what and where.

End the turn after spawning; the report arrives as a task notification. Multiple PRs whose CI went green together get their Reviewers spawned in one message.

## Step 3 — Read the diff (Reviewer mode)

1. `Read` the packet digest first (it's in the brief or at `<scratch>/packet.md`). It tells you which files are implementation, which are tests, which are generated, whether a migration shipped, and which ADRs the changed paths hit.
2. `Read` `<scratch>/diff.patch` — the full hand-written diff, generated and vendored files already split out into `diff-generated.patch`. Read it once, in order. For a large PR, read per-file via `git diff <base>...<head> -- <path>` in the order the packet's table lists them (implementation before tests before docs), so each test is read with its subject already in mind.
3. Pull surrounding context only where a hunk can't be judged in isolation: `sed -n '<start>,<end>p' <file>` on the head ref, not `cat`. A whole-file read is justified only for a file the PR created.
4. Skip `diff-generated.patch` unless the packet flags something unexpected in it (a lockfile change with no dependency change in the manifest, a regenerated file that shouldn't have changed).

## Step 4 — Judge

Work through these in order; each becomes a section of the report. The packet supplies the *facts* for a section; the Reviewer supplies the *finding*.

- **Spec adherence.** Every acceptance criterion and every "points to scrutinize" item: met, partially met, or missing — cite the hunk. Then each flagged judgment call: does it hold up against the actual diff? Sometimes the Implementer reasoned from intent and the diff shows the call was wrong; sometimes the Reviewer is missing why a parameter is reserved for an unmerged downstream issue — say which, and why.
- **Correctness and edge cases.** Off-by-ones, nil/empty/zero paths, error propagation, concurrency, hidden state, ordering assumptions, anything the tests wouldn't catch. A finding here needs a concrete failing input, not a feeling.
- **Test coverage.** The packet lists the test names added. Map them to the ACs. Name the AC or behavior with no test. If the issue has UJT-translated tests, check they translate the UJT prose faithfully rather than papering over a divergence. Tests that assert implementation details rather than observable behavior are a nit unless they would break the next refactor of the same area (then a finding).
- **Vocabulary and domain alignment.** The packet lists new identifiers and flags any that match a `_Avoid_:` alias or aren't in `CONTEXT.md`. For each: is it a domain concept (then it must be in `CONTEXT.md`, added in this PR) or a purely technical name (fine)? A domain term introduced without a `CONTEXT.md` update, or an identifier that uses an avoided alias, is a **Blocker**, not a nit — drift compounds across parallel PRs. A load-bearing decision made silently where an ADR was warranted is also a Blocker.
- **Migration safety** (only if the packet shows a schema change). Reversibility, data backfill, ordering against other in-flight PRs, whether existing fixtures still load.
- **Idiom and style nits.** Anything mechanical the Main thread can fix inline in under ~50 LOC. Keep this list short; the Main thread reads it as a to-do.

## Step 5 — Visual diff gate (only when a Comp Reference exists)

This gate is the reason Comps exist. A text-only review of a UI PR is the failure mode this skill was written to prevent.

1. For each screen the PR touches, the packet either has a captured screenshot at `<scratch>/shots/<name>.png` or says capture failed.
2. If captured: `Read` the Comp PNG from the Design bundle and the captured PNG. Compare layout, spacing, color, typography, content placement, and empty/error states the Comp defines.
3. If capture failed (auth wall, client-side render the headless capture couldn't wait for): use Chrome MCP yourself — `navigate` to the URL, then screenshot. Do **not** call page-text, find, or accessibility-tree tools; you are comparing pixels, and those dumps cost more than the screenshot. Sign-in walls are a stop: report the gate as blocked and let the Main thread handle auth.
4. Every discrepancy is **Request changes** unless the Implementer flagged it as an intentional deviation with rationale — then rule on the rationale. Where the Comp and the issue text disagree, the Comp wins.
5. If the issue has no `## Comp Reference`, or it reads `Foundation — no screen rendering`, omit this section entirely. Don't write "N/A".

## Step 6 — Report

Target 400 words; hard cap 500 for a large PR. Sections in this order, headings exact — omit Visual diff and Migration safety when they don't apply:

```
## Spec adherence
## Visual diff            (per screen: PASS or discrepancy list)
## Correctness & edge cases
## Test coverage
## Vocabulary & domain alignment
## Migration safety
## Idiom & style nits
## Verdict
<one paragraph: the decisive findings and what would flip the verdict>

verdict: approve | approve-with-nits | request-changes
posted: none
```

- `approve` — nothing to change.
- `approve-with-nits` — only items the Main thread can fix inline without a Fix agent.
- `request-changes` — at least one real bug, a missed AC, a Visual diff discrepancy, or a vocabulary Blocker. Lead the Verdict paragraph with it.

The `verdict:` and `posted:` lines are the last two lines of the report, exactly as spelled. If anything was posted to the tracker, `posted:` names it; the default is `none`.

## After the report (Main-thread mode)

Hand the report to Stage 4 of the calling flow, or to the user. Before forwarding a `request-changes` finding, check it against the Implementer's flagged judgment calls — if the Implementer already named the call and the Reviewer disagrees on a design question rather than a bug, that goes to the user, not to a Fix agent. Delete the scratch dir after the PR merges or the review is abandoned; leave it in place while fixes are in flight so a re-review can diff against the same base.

A re-review after fixes reuses the flow: re-spawn `review-prep` (the diff changed) and a fresh Reviewer briefed with the previous report's findings, asking only whether each is resolved. Cap that report at 150 words.

## Common failure modes

- **Reviewer fetches the PR via MCP anyway** and the diff enters its context twice. The brief must say the diff is in the packet; if the packet is missing, the Reviewer runs the git commands, not the MCP call.
- **Generic review with no spec context.** "Looks idiomatic, ship it." Caused by a brief without the issue body and points to scrutinize. The Spec adherence section must cite ACs by ID; if it can't, the brief was thin — say so in the report rather than padding.
- **Visual diff section missing** on a PR whose issue has a Comp Reference. The Main thread sends the Reviewer back; the packet's screenshot paths (or the app URL) go in the follow-up.
- **Verdict line paraphrased** (`Verdict: Approve with minor nits`). The calling flow keys on the exact spelling; fix the line, not the flow.
- **Vocabulary drift filed as a nit.** It's a Blocker. A nit is fixed inline and forgotten; a Blocker gets the `CONTEXT.md` entry landed in the same PR.
- **Main thread reads `diff.patch` "just to check".** That is the whole review's context cost landing on the orchestrator. Trust the packet digest and the Reviewer's report; if you doubt a finding, ask the Reviewer for the hunk.
