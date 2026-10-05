---
name: ship-issue
description: "Drive a tracked issue from 'ready to implement' to 'merged on main' via a parallel-agent flow — spawn an Implementer subagent in an isolated git worktree, gate on green CI, spawn a Reviewer subagent, apply review findings, gate on green CI again, then merge (role→model mapping in MODELS.md). Use this skill whenever the user asks to implement, ship, build, work on, kick off, or merge a specific tracked issue ('implement #308', 'ship issue 42', 'send this to an agent', 'kick off the verdict scorer ticket', 'let's land the negation primitive'), asks to hand an issue to a specific model or agent, references the agent-driven flow we've been using, or asks to take a ticket end-to-end. Also use it when the user wants to chain implementation, review, and merge as one continuous flow rather than handling each gate manually. Default to invoking this skill any time the user names a single issue and signals intent to land it."
---

# Ship Issue

Take a single tracked issue from "ready to implement" to "merged on main" using an Implementer → Reviewer agent pipeline (current role→model mapping: `MODELS.md` at the repo root). The skill exists because doing this by hand burns context on git plumbing, polling CI, and writing reviewer prompts — each step is mechanical, but the sequence has gates that must be respected (CI must pass before review; review must clear before merge).

## Model split — judgment vs. execution

The flow splits roles across model tiers: a judgment model thinks and arbitrates, an execution model types. The current role→model mapping — and the capability rationale behind it — lives in `MODELS.md` at the repo root; change it there first when models churn. The shape below survives any particular mapping:

- **Main thread — planner and arbiter, on the judgment model.** Reading the issue, building the implementer brief, briefing the reviewer, arbitrating between flagged judgment calls and reviewer findings, applying inline fixes, deciding when to merge. Anything that requires holding the spec, the addenda, the parent design, the dependency graph, and the in-flight branches in mind at once. Don't downgrade the main thread — the cross-cutting context is exactly what the strongest judgment model is for. (Skills can't set the session model; the user picks it via `/model`.)
- **Implementer subagents — execution.** The Implementer does its best work when the brief is concrete: read-list spelled out, scope and out-of-scope enumerated, decisions pre-locked, edge cases pre-resolved, repo conventions named. The brief should let the implementer move fast and write idiomatic code without burning tokens on design deliberation. If you find yourself writing "use your judgment on X" in an implementer brief, stop and decide X on the main thread first — that's a Main-thread judgment task masquerading as execution.
- **Reviewer subagents — judgment.** Review is what the strongest model is for: spec adherence, design soundness, hidden-state risks, what tests are missing, whether a flagged judgment call holds up against the actual diff. Weaker reviewers tend to under-scrutinize, pattern-matching toward "approve" — never run the Reviewer on a weaker model than the Implementer.
- **Inline fixes on the main thread.** Small mechanical fixes (lint nits, dead code, doc typos) — edit in the worktree directly. A subagent's per-spawn startup cost beats the fix size when the change is under ~50 LOC.

The implicit contract: the judgment model does the *thinking*, the execution model does the *typing*. When that contract slips — the Implementer is making design calls, or the Main thread is dispatching trivial edits to a subagent — the flow loses its edge.

## When to use

Use this skill when:
- The user names a specific issue and signals "ship it" / "implement it" / "send to an agent" / "let's land this"
- The user wants to merge a PR that's already up but hasn't been reviewed yet
- The user asks for the "agent-driven flow" or refers to a previous instance of this loop

Don't use this skill for:
- **Research/design issues** that produce specs and sub-issues rather than code. Those have a different shape (an agent drafts spec → user reviews → sub-issues filed). Treat planning as a *precursor* to this skill — once sub-issues exist, this skill takes one of them and ships it.
- **Multi-issue umbrellas** where the deliverable is several PRs at once. Run this skill once per sub-issue.
- **Tasks the user wants to drive themselves.** If they just want a code change made directly, don't spin up an agent — edit the files.
- **Issues that haven't been triaged.** This skill expects issues already in `ready-for-agent`. If the issue is `needs-triage` or `needs-info`, refuse and route through [[triage]] first. An under-briefed Implementer costs more than the triage detour.

## Prerequisites

The skill assumes:
- The issue is on **Gitea** (preferred) or GitHub. Adapt tool calls accordingly.
- For Gitea: `mcp__gitea__issue_read`, `mcp__gitea__pull_request_write`, `mcp__gitea__actions_run_read` are available (load via `ToolSearch` as needed).
- The repo is checked out locally; `git worktree` works.
- The `Agent` tool supports `isolation: "worktree"` and a `model:` override (current role→model mapping and valid aliases in `MODELS.md`).
- The user is in **auto mode** or has otherwise indicated they want autonomous execution. If not, surface gates to the user before each transition (don't auto-merge without confirmation).

Before starting, scan repo memory (`MEMORY.md` and the linked files) for things like:
- Merge style (squash vs. merge-commit). Some repos only accept one style — passing the wrong `merge_style` to `pull_request_write` returns 405.
- CI gates that aren't implied by the obvious lint command (e.g. on Go repos, gofmt is often a separate gate — golangci-lint clean does not imply gofmt clean).
- Branch naming conventions and commit message style (read `git log --oneline -20` to confirm).
- Any "umbrella PR" rules around close-directives.

These details change the implementer's brief; if you skip the memory pass you'll spawn an agent that opens a PR CI rejects.

## The flow

Five stages. Each stage has a gate that must clear before the next begins. **Don't collapse stages.** If you spawn the implementer and the reviewer in the same turn, the reviewer will read mid-implementation code.

### Stage 0 — Sync local main (preflight)

**Before spawning the implementer**, sync local `main` against the remote. The `Agent` tool's `isolation: "worktree"` creates the worktree from local HEAD, not from `origin/main`. If main has moved since you last pulled (very likely if you've recently merged sibling PRs from this repo), the implementer will branch off a stale base, do good work that conflicts on push, and you'll have to rebase manually.

```bash
git fetch origin main
git checkout main && git merge --ff-only origin/main
```

Or if you know your working tree is clean and on main:

```bash
git pull --ff-only origin main
```

Skip this only when you've literally just pulled in the same shell session and nothing has merged since. When in doubt, run it — the cost is one round-trip; the cost of not running it is a manual rebase mid-flow.

**This step does NOT apply to the reviewer.** The reviewer reads the PR diff against current main via the Gitea API, not from a worktree, so it always sees the up-to-date base regardless of local state.

### Stage 1 — Implementation

Spawn one **Implementer** agent in an isolated worktree.

```
Agent({
  description: "Implement #N (short scope)",
  subagent_type: "general-purpose",
  model: "opus",             // Implementer — current mapping in MODELS.md
  isolation: "worktree",
  run_in_background: true,
  prompt: <see brief below>
})
```

Brief the agent with:
- The issue number and a one-line scope summary
- A **read-first list**: the issue body, any parent design comments (spec + addenda), prerequisite-PR code that just landed (so the agent reads consumed APIs), and ~1–3 existing files that anchor the repo's idiomatic patterns
- **`CONTEXT.md` and the ADRs in `docs/adr/` that touch the area** — the implementer must read both before writing code, and must use the glossary's vocabulary in code identifiers, comments, commit messages, and PR description. This is the contract that prevents vocabulary drift across PRs. If the implementer introduces a domain term not in `CONTEXT.md`, the implementer must add it in the same PR (using the format in [[language/grill-with-docs/references/CONTEXT-FORMAT.md]]).
- **Comp reference** — if the issue's `## Comp Reference` section references Comp files in the Design bundle, the implementer **`Read`s the screenshot PNGs (visual targets — Claude sees images) and the prototype HTML/JSX (design tokens, component structure) to match the rendered output**: layout, spacing, color, typography, component structure. The Comp is the visual source of truth, not the textual description. When the Comp and the text disagree, the Comp wins (flag the discrepancy in the report-back so the Reviewer can verify). If no Comp is referenced, the issue is backend-only or the Design bundle is incomplete — note which.
- **Test discipline** — if the issue body lists testable behaviors (most do), the implementer runs **`/tdd` discipline**: one test → one implementation → repeat. Tests verify observable behavior through public interfaces, not implementation details. Do not batch tests at the end — that produces tests of imagined behavior. See [[tdd]] for the full discipline. If the issue is a bug fix, the implementer instead runs **`/diagnose`** (build a deterministic feedback loop first, then the regression test, then the fix). See [[diagnose]].
- The **scope** (what's in) and **out of scope** (what to defer to follow-up tickets)
- Repo conventions from the memory pass: every CI gate the agent must run locally (e.g. a formatter gate separate from the linter), branch naming (e.g. `feat/<N>-<slug>`), commit message style, the repo's merge style, close-directive rules (e.g. no "Closes #parent" on sub-issue PRs), no auto-generated footers
- The push target (`origin` for Gitea — the GitHub remote, if present, is usually a mirror)
- Explicit instruction: open the PR via `mcp__gitea__pull_request_write`, **do not merge**, stop at "PR open and CI running"
- Reporting requirements: PR URL, branch name, files touched, confirmation that every local gate from the brief (e.g. gofmt + golangci-lint + go test on a Go repo) ran clean, any spec deviations or judgment calls, **any updates made to `CONTEXT.md` or `docs/adr/` in the same PR**, **and per-screen Comp match status** (for each linked Comp: matched / diverged-intentionally-with-rationale / no Comp linked). The report is a compact list capped at ~200 words — the main thread needs the facts above, not a narrative of the work

Run in the background and end your turn. The user gets a notification on completion.

When the agent reports back, surface to the user:
- PR URL
- One-paragraph summary of what shipped
- Any judgment calls or spec deviations the agent flagged

### Stage 2 — CI gate (first pass)

Check the PR's CI status via `mcp__gitea__actions_run_read` (`list_runs` filtered by head SHA, then `get_run` on the matching id).

If CI is **green**: proceed to Stage 3.

If CI is **failing**: delegate log reading to the `ci-check` Utility agent (spawn it with the repo, PR number, and head SHA; it returns a classified digest with the minimal failing excerpt) rather than pulling `get_job_log_preview` output into Main-thread context. If its report ends `confidence: partial` or `not-found`, re-spawn the same brief once on the Escalation tier from `MODELS.md`; if that also fails, read the log yourself. Most failures fall into:
- **gofmt / lint nits** the agent didn't run locally → fix inline, commit, push
- **Real test failures** → fix inline if obvious, otherwise SendMessage / spawn a new agent with the failure context
- **Schema migration issues** → usually need agent re-engagement

If CI is **in progress**: use `ScheduleWakeup` (180–270s, stays in cache window) to come back and recheck. Don't poll inline.

### Stage 3 — Review

If the issue has a `## Comp Reference`, start the app in the implementer's preserved worktree before spawning the reviewer. The reviewer is read-only (no worktree) and cannot run the app itself:

1. `cd` into the implementer's worktree path
2. Run the app startup command (from the project's `CLAUDE.md` or `MEMORY.md`)
3. Wait for the health endpoint or poll the app URL until it responds
4. Note the app URL for the reviewer brief

If no `## Comp Reference` exists, skip this — the reviewer doesn't need the running app.

Then assemble the Review packet: spawn the `review-prep` Utility agent (`subagent_type: "ai-tools:review-prep"`, foreground — the reviewer brief depends on it) with the repo, PR number, base branch, a scratch dir (`/tmp/review-<repo>-<N>`), and — if a Comp Reference exists — the app URL and the routes to screenshot. The packet writes the diff to disk and returns a ~300-word digest (changed-file table, new identifiers vs. `CONTEXT.md`, ADR hits, tests added, migration presence, PR hygiene, screenshot paths). Keep the digest; it is also your early warning for missing `Resolves #N`, unwanted footers, and shared-file conflicts. Escalation ladder applies (`agents/README.md`): one retry on the Escalation tier (`MODELS.md`) on `partial` / `not-found`, then run the packet commands inline — but never `cat` the diff into Main-thread context. The full procedure is [[review]]; this stage is its Main-thread mode.

Spawn one **Reviewer** agent. Don't run it in a worktree — review is read-only.

```
Agent({
  description: "Review PR #N",
  subagent_type: "general-purpose",
  model: "fable",            // Reviewer — current mapping in MODELS.md
  run_in_background: true,
  prompt: <see brief below>
})
```

Brief the reviewer with:
- The PR number and a one-line scope summary
- The **Review packet path and digest** (paste the digest — it's small), and the instruction to invoke the `ai-tools:review` skill via the `Skill` tool with `PR #N, base <branch>, packet <path>`. If the `Skill` tool can't resolve it in the subagent, the reviewer follows the report shape from [[review]] manually — it does **not** re-fetch the diff via MCP; the diff is in the packet
- **Token discipline**, stated explicitly: the diff is in the packet, so no `pull_request_read` for it; `CONTEXT.md`, the issue body, and the ADRs are in this brief, so no re-reading them from disk; implementing files are read in ranges around hunks, never whole (unless the PR created the file)
- The same context the implementer had (issue body, parent spec/addendum, **`CONTEXT.md`, and relevant ADRs**) so the reviewer can judge spec adherence and vocabulary alignment
- **Specific points to scrutinize**: any judgment calls the implementer flagged, any spec sections that are subtle (e.g. matrix tables, formula tie-breaks), migration safety if a schema bump shipped, **vocabulary drift (identifier names that don't match `CONTEXT.md`; new domain concepts introduced without a `CONTEXT.md` update; ADR-relevant decisions made silently)**
- **Visual diff gate** — if the issue has a `## Comp Reference`, the reviewer **must** compare the running app to each referenced Comp. The main thread has already started the app and provides the URL in this brief. Steps: (1) navigate to the app URL provided, (2) navigate to each screen the PR touches, (3) screenshot the rendered state via Chrome MCP, (4) `Read` the Comp screenshot from the Design bundle, (5) compare layout, spacing, color, typography, and content placement. Discrepancies are **Request changes** unless the implementer flagged them as intentional deviations with rationale. This is the gate that was missing when Comps existed but were never diffed — without it, implementers rebuild from textual specs and diverge silently. If no Comp is referenced, note it in the review but do not block.
- Output expectations: the [[review]] report shape — sections Spec adherence / **Visual diff** (Comp vs. app — per screen, PASS or discrepancy list; omit this section if no Comp Reference exists) / Correctness & edge cases / Test coverage / **Vocabulary & domain alignment** / Migration safety if applicable / Idiom & style nits / Verdict, capped at ~400–500 words depending on PR size, ending in the two machine-readable lines `verdict: approve | approve-with-nits | request-changes` and `posted: none`
- **Do NOT post review comments to Gitea.** Findings come back to the main thread and the user decides what to act on. If anything is posted anyway, the `posted:` line must say what and where.

Run in the background and end your turn.

### Stage 4 — Apply review findings

When the reviewer reports back, key on its `verdict:` line (the second-to-last line of the report; if it's missing or paraphrased, ask the reviewer for it rather than guessing). It is one of:
- **approve** → straight to Stage 5
- **approve-with-nits** → fix the nits inline (small mechanical edits; don't spawn another agent for cosmetic stuff). Commit + push. Then Stage 5.
- **request-changes** → there's a real bug, a missed AC, a Visual diff discrepancy, or a vocabulary Blocker. Decide whether the fix is small enough to do inline, or warrants re-engaging the implementer. Re-engagement is rarely necessary for a single bug; inline is usually faster.

After fixes, re-review per [[review]]: re-spawn `review-prep` (the diff changed) and a fresh reviewer briefed with the previous findings, asking only whether each is resolved. Delete the scratch dir once the PR merges.

When the reviewer flags a finding, **always check whether the implementer already noted it as a known judgment call.** If yes, the question is whether the call was correct — sometimes the reviewer is right that the call is wrong (e.g. they have access to the actual diff, the implementer was reasoning from intent).

For inline fixes: edit on the worktree path the implementer was working in (it's preserved post-completion until cleanup), commit with a `fix(...): <one-line> Reported by PR review on #N.` style message, and push.

### Stage 5 — CI gate (final pass) and merge

After fix commits, check CI again the same way as Stage 2.

When CI is green:

```
mcp__gitea__pull_request_write({
  method: "merge",
  owner: "<user>",
  repo: "<repo>",
  index: <PR number>,
  merge_style: "squash",   // the repo's style from the memory pass
  delete_branch: true,
})
```

After merge, summarize to the user: PR landed, deferred nits if any, then **suggest what to ship next** (see Stage 6).

### Stage 6 — Suggest next issue(s)

After the merge summary, fetch open issues on the same repo and present a short table the user can pick from. This is the natural seam in the loop: the user just shipped one ticket and is deciding whether to keep going. Don't skip it — silent termination forces the user to context-switch into Gitea to figure out what's next.

Fetch with `mcp__gitea__list_issues` (state=open, type=issues, sort by recently-updated or by issue number — whatever surfaces the in-flight work). Filter out anything that's clearly a tracking/umbrella issue, a research/design issue that produces sub-issues rather than code, or anything labelled `blocked` / `waiting`.

Present a table with columns: **#**, **Title** (truncated to ~70 chars), **Why now** (one short clause — "natural follow-up to #346", "unblocks #N", "smallest scope of the open set", "depends on nothing else open", etc.). Cap the table at ~5 rows; pick the ones most worth picking up next, not the full backlog. Bias toward:

1. Direct follow-ups to the issue just merged (the implementer or reviewer may have flagged a deferred follow-up in their reports).
2. Sub-issues whose dependencies are now unblocked by the merge.
3. Small, well-specified tickets the user can hand straight back to this skill.

Then call out a **recommendation**: one or two sentences naming the issue(s) you'd ship next and why. If the issue(s) you're recommending touch the same area of the code and could share a single worktree/PR without losing reviewability, say so explicitly — "#A and #B both edit `internal/foo/bar.go` for the same enum addition, could bundle into one PR." If the recommended issues are independent, do NOT propose bundling — bundling is only a suggestion when the *recommended* set naturally collapses, never the criterion for selection. The default is one issue per PR.

End with a one-line CTA: "Reply `ship N` to kick off the next one, or `ship N,M` to bundle." Don't auto-spawn — the user picks.

## Parallelism

**Multiple sub-issues with independent dependency edges should ship in parallel.** Spawn N Implementers (each in its own worktree) in a single message with multiple `Agent` tool calls. Same for reviewers. Don't stagger them serially — that throws away the main reason to use this flow.

Watch for **shared-file conflicts** between parallel branches. Common culprits: `internal/config/config.go` (multiple PRs add new options), top-level `Makefile`, schema files. If you see two branches touching the same file, sequence the merges so the second one gets a clean rebase.

## Common failure modes

- **Implementer reports "tests pass" but skipped a lint/format gate.** The test command alone is necessary but not sufficient (Go example: `go test ./...` passing says nothing about `golangci-lint` or gofmt). The brief must enumerate every gate CI runs; look for each in the report-back, and if one is missing, run it yourself before requesting review.

- **Implementer's PR description includes Claude footers.** The repo doesn't want them. The skill brief says no, but agents sometimes default-include. Check and amend the PR body via `pull_request_write` `update` if needed.

- **Reviewer doesn't get the spec context** and produces a generic Go review. The reviewer brief must include the parent design comment URLs and call out specific spec sections to scrutinize (matrix rows, formula tie-breaks, sentinel error contracts). Without these, reviews regress to "looks idiomatic, ship it" and miss real bugs.

- **Reviewer forages instead of reading the packet** — fetches the PR via MCP, re-reads `CONTEXT.md` and every ADR, `cat`s whole files. The review is fine but costs two to three times what it should on the judgment model. The brief must name the packet path and state the token discipline; if the packet was never assembled, that's the Main thread's miss, not the reviewer's.

- **Reviewer skips the Visual diff gate** even though a Comp exists. The review comes back with only text-based findings and no Visual diff section. Send the reviewer back with explicit instructions to screenshot the running app and compare to the Comp. This is the highest-leverage gate — a textual review that misses a visual divergence is the exact failure mode the gate exists to prevent.

- **Reviewer's flagged "real bug" is actually intentional contract-shape.** Always check the implementer's flagged judgment calls before forwarding the reviewer's finding. Sometimes the reviewer is right (a 0.5 stub that always wins a tiebreak isn't a 50/50 split); sometimes they're missing why a parameter is reserved for an unmerged downstream ticket.

- **`mergeable: false` after CI passes.** This is almost always Stage 0 missed: the implementer branched off stale local `main`. Recovery: `cd` into the implementer's worktree, `git fetch origin main`, `git rebase origin/main`, resolve conflicts (typically in `internal/config/config.go` if multiple PRs added new options), re-run all local gates, then `git push --force-with-lease`. Wait for CI to re-green before merging.

- **CI flakes on the second push.** A push that ought to be a no-op (rebased, squashed) sometimes triggers a re-run that hits a transient failure. Re-trigger via an empty commit or a fresh push before assuming a real failure.

- **Merge fails with 405.** Some repos restrict which merge styles they accept, and the `pull_request_write` default is `merge` — always pass the repo's accepted style (from the memory pass) explicitly.

## Stopping and escalating

Some moments warrant pausing for the user even in auto mode:
- **Reviewer requests changes on something that's a design call**, not a bug. The implementer made a defensible choice; the reviewer disagrees. The user should arbitrate.
- **CI fails on something repo-wide** (not the new PR). Schema migrations interact with other tests; an "unrelated" failure may actually be your migration. Surface the failure and the user's option set.
- **Multiple parallel PRs conflict on shared files.** Resolve them in order, but check with the user on conflict-resolution strategy if more than one of them touches semantic structure (not just formatting).
- **The PR's scope balloons mid-implementation** because the implementer found a related problem. Have them stop and surface the scope creep — don't let a "ship #308" turn into "rewrite half the storage layer."

## Memory awareness

Before each new run of this skill in a repo, check `MEMORY.md` for:
- Merge style for that repo (squash vs. merge)
- Any feedback notes about CI gates not visible in `.gitea/workflows` or `.github/workflows`
- Branch naming conventions
- Any specific reviewer or implementer instructions the user has standardized on

Update `MEMORY.md` afterward if a new convention surfaced — e.g., a CI gate the implementer should have run, or a recurring style nit the reviewer always catches.
