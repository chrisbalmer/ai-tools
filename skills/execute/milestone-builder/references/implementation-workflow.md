# Per-Issue Implementation Workflow

Detailed steps for taking a single issue from "ready in the current tier" to "merged into the milestone branch" using an Implementer→Reviewer→Fix-agent pipeline (role→model mapping in `MODELS.md` at the repo root). Each stage has a gate that must clear before the next begins. **Don't collapse stages.** If you spawn the implementer and the reviewer in the same turn, the reviewer will read mid-implementation code.

This workflow runs inside the larger milestone flow defined in `SKILL.md` — branches target the **milestone branch**, not main, and the reviewer is judging spec adherence against the issue body, not against main-branch contracts.

## Prerequisites per issue

You already have, on the main thread:

- The cached issue body (from the Fetch and Parse step)
- The repo's CLAUDE.md and MEMORY.md content
- Repo conventions: merge style, commit style, branch naming, footer rules, CI gates not visible in workflow files (e.g. gofmt as a separate gate from golangci-lint)
- The list of ready issues in the current tier (to decide on parallel dispatch)

## Stage 0 — Sync the milestone branch (preflight)

**Before spawning any implementer in this tier**, sync the local milestone branch against its remote. The `Agent` tool's `isolation: "worktree"` creates the worktree from local HEAD, not from `origin/<milestone-branch>`. If a previous issue in this tier just merged on the remote, the new implementer will branch off stale local state and conflict on push.

```bash
git checkout milestone-<ID>-<kebab-name>
git pull --ff-only origin milestone-<ID>-<kebab-name>
```

Run this once per tier (not once per issue) — the milestone branch only advances when a PR merges, and multiple ready issues in the same tier should all branch from the same synced HEAD.

This step does NOT apply to the reviewer or fix-agent stages. Reviewers read the PR diff via the Gitea API, and fix agents work in the worktree the implementer already left behind.

## Stage 1 — Implementation (Implementer, in parallel where possible)

For every ready issue in the current tier, spawn one Implementer agent in an isolated worktree. **Spawn the whole tier in a single turn**, with multiple `Agent` tool calls in the same message. The exception is shared-file conflicts: if two ready issues touch the same file, sequence them instead (see SKILL.md "shared-file conflicts").

```
Agent({
  description: "Implement #<N> (short scope)",
  subagent_type: "general-purpose",
  model: "opus",             // Implementer — current mapping in MODELS.md
  isolation: "worktree",
  run_in_background: true,
  prompt: <see brief below>
})
```

Brief the agent with:

- **Issue context** — issue number, one-line scope summary, and the full cached issue body (description, AC, technical notes, files-likely-touched, **the `## UJTs to Translate` list** from Phase 8 if the design process produced it)
- **Branch shape** — base branch is `milestone-<ID>-<kebab-name>`; feature branch should be `issue-<N>-<short-kebab-description>`; PR targets the milestone branch, not main
- **Read-first list** — paths in the repo that anchor idiomatic patterns for this kind of change (1–3 files), plus any prerequisite-issue PRs that just landed in the milestone branch so the agent reads consumed APIs, **plus the UJT source files listed in the issue body** (the implementer reads the prose to know what to translate), **plus `CONTEXT.md` and any ADRs in `docs/adr/` that touch the area** (vocabulary and locked-in decisions the implementer must honour)
- **Vocabulary contract** — the implementer must use `CONTEXT.md` vocabulary in code identifiers, comments, commit messages, and PR description. If the issue introduces a new domain concept, the implementer adds it to `CONTEXT.md` in the same PR (format: [[language/grill-with-docs/references/CONTEXT-FORMAT.md]]). If the issue requires a load-bearing decision (hard-to-reverse, surprising, real trade-off), the implementer drops an ADR into `docs/adr/0NNN-<slug>.md` (format: [[language/grill-with-docs/references/ADR-FORMAT.md]]). Drift is a reviewer-Blocker, not a nit.
- **Comp reference** — if the issue's `## Comp Reference` references Comp files in the Design bundle, the implementer `Read`s the screenshot PNGs (visual targets — Claude sees images) and the prototype HTML/JSX (design tokens, component structure) to match the rendered output: layout, spacing, color, typography, component structure. The Comp is the visual source of truth; when it disagrees with the textual description, the Comp wins (flag the discrepancy in the report-back). If no Comp is referenced, the issue is backend-only or the Design bundle is incomplete — note which.
- **Test discipline** — implementer runs **[[tdd]]** for new behaviors (one test → one implementation → repeat; tests verify observable behavior, not implementation details; never batch tests). For bug-fix issues, the implementer runs **[[diagnose]]** instead (deterministic feedback loop first, then regression test, then fix).
- **Scope** — what's in (the AC), and what's out of scope (defer to follow-up tickets and call them out)
- **UJT contract** — for every UJT listed in the issue's `## UJTs to Translate` section, the agent must translate to a runnable form (XCUITest / Playwright / etc. — read the project's `CLAUDE.md` for the target convention) and commit the translation in the same PR as the production code. The PR is not done until all listed UJTs pass. If a translated UJT fails for a reason that looks like spec drift (not a code bug), the agent stops, reports the drift to the main thread, and lets the orchestrator triage (see Stage 2.5)
- **Repo conventions** — commit message style (e.g., `Resolves #N`), no `Co-Authored-By` footers, no Claude footers in PR body, merge style of the repo, any CI gates the agent must run locally (e.g. Go repos where `gofmt` is a separate CI gate from `golangci-lint`)
- **Push target** — `origin` for Gitea (the GitHub remote, if present, is usually a mirror)
- **Explicit instructions** — (1) open the PR via `mcp__gitea__pull_request_write` with base set to the milestone branch and `References #<N>` in the body; (2) do not merge; (3) stop once the PR is open and CI is running (including UJT-translated tests)
- **Reporting requirements** — PR URL, branch name, files touched, confirmation that all local gates ran clean, **per-UJT status (translated + passing / translated + failing-with-drift / translated + failing-as-code-bug)**, **per-screen Comp match status** (for each linked Comp: matched / diverged-intentionally-with-rationale / no Comp linked), **any new terms added to `CONTEXT.md` or new ADRs landed in `docs/adr/`**, any spec deviations or judgment calls the reviewer should scrutinize. The report is a compact list capped at ~200 words plus the per-UJT and per-screen status lines — not a narrative of the work

Run in the background and end the turn (or proceed to brief the next implementer if more are in the tier). The main thread gets a notification per agent on completion.

When each agent reports back, capture for later use:
- PR URL and number
- Branch name
- Files touched
- Any flagged judgment calls (these go into the reviewer brief)

## Stage 2 — CI gate (first pass)

For each implementer that just reported "PR open and CI running", check CI via `mcp__gitea__actions_run_read` (`list_runs` filtered by head SHA, then `get_run` on the matching id).

- **CI green** → proceed to Stage 3 for this PR
- **CI failing** → delegate log reading to the `ci-check` Utility agent (one spawn per failing PR; brief it with repo, PR number, head SHA) and act on its digest rather than pulling `get_job_log_preview` output into Main-thread context. A `confidence: partial` / `not-found` report gets one Escalation retry on the Escalation tier from `MODELS.md`, then the main thread reads the log itself. Most failures fall into:
  - **Lint/format nits** the implementer didn't run locally → fix inline on the main thread (edit in the worktree, commit, push). Cheaper than spawning a Fix agent.
  - **Real test failures** → fix inline if obvious (under ~50 LOC). Otherwise SendMessage the original implementer or spawn a new Fix agent with the failure context.
  - **Schema/migration issues** → usually need agent re-engagement (a Fix agent) because they require reading state.
- **CI in progress** → use `ScheduleWakeup` (180–270s, stays inside the prompt cache TTL) to come back and recheck. Do NOT inline-sleep or inline-poll — that burns the main thread's tokens for no work.

If checks fail more than twice on the same issue, stop and report to the user.

## Stage 2.5 — UJT drift triage

If the implementer reported one or more UJTs as `failing-with-drift` — meaning the test translated faithfully from the prose but failed because the prose disagrees with shipped reality — triage on the main thread:

- **Read both sides** — the UJT prose (from `User Journey Tests/<Epic>.md` in the vault) and the actual code path the test exercised. The implementer's report should name both.
- **Decide which is right** — usually the code, because it's been through implementation pressure that the design predates. But sometimes the code grew sideways and needs pulling back.
- **Fix the right side** —
  - **Design is wrong** → file a design-drift issue in the same tracker (label `documentation`, scope to the affected epic), and update the UJT/AC in the vault's design artifacts to match reality. Optionally update the translated test in the implementer's worktree to match the new contract. Re-run; expect green.
  - **Code is wrong** → escalate the finding to the implementer (SendMessage with the specific drift) or spawn a Fix agent. Re-run.
- **Don't merge a PR with skipped UJTs.** A `failing-with-drift` UJT must either be fixed (code) or have its design-side counterpart corrected and the test updated, before Stage 5.

This stage is where the design-vs-code feedback loop actually closes — most projects' "the docs are out of date" problem comes from skipping it.

## Stage 3 — Review (Reviewer, no worktree)

When a PR's CI is green:

1. If the issue has a `## Comp Reference`, start the app in the implementer's preserved worktree before spawning the reviewer. The reviewer is read-only (no worktree) and cannot run the app itself. `cd` into the worktree, run the app startup command, wait for readiness, and note the app URL for the reviewer brief.
2. Assemble the Review packet: spawn the `review-prep` Utility agent (`subagent_type: "ai-tools:review-prep"`, foreground) with the repo, PR number, the milestone branch as base, a scratch dir (`/tmp/review-<repo>-<PR>`), and — if a Comp Reference exists — the app URL and routes to screenshot. Keep the ~300-word digest; it flags missing `Resolves #N` and footers, and its file table is what you compare across the tier's in-flight packets to spot shared-file conflicts. Escalation ladder applies (`agents/README.md`). This stage is the Main-thread mode of [[review]].
3. Spawn one Reviewer agent. Reviewers are read-only — no worktree.

```
Agent({
  description: "Review PR #<PR> (issue #<N>)",
  subagent_type: "general-purpose",
  model: "fable",            // Reviewer — current mapping in MODELS.md
  run_in_background: true,
  prompt: <see brief below>
})
```

Brief the reviewer with:

- **PR number** and a one-line scope summary
- **Issue body** (cached), **`CONTEXT.md`, and ADRs in `docs/adr/` that touch the area** — so the reviewer can judge spec adherence and vocabulary alignment
- **Implementer's flagged judgment calls** — call these out explicitly and ask the reviewer to evaluate whether each call holds up against the actual diff
- **Specific points to scrutinize** — any subtle spec sections (matrix tables, formula tie-breaks, sentinel error contracts), migration safety if a schema bump shipped, cross-cutting concerns this issue touches, **the UJT-translated tests in the PR (do they faithfully translate the UJT prose, or did the implementer paper over a real divergence?)**, **vocabulary drift (identifier names that diverge from `CONTEXT.md`; new domain concepts introduced without an inline `CONTEXT.md` update; load-bearing decisions made without an ADR)**
- **Visual diff gate** — if the issue has a `## Comp Reference`, the reviewer **must** compare the running app to each referenced Comp. The main thread has already started the app and provides the URL in this brief. Steps: (1) navigate to the app URL provided, (2) navigate to each screen the PR touches, (3) screenshot the rendered state via Chrome MCP, (4) `Read` the Comp screenshot from the Design bundle, (5) compare layout, spacing, color, typography, and content placement. Discrepancies are **Request changes** unless the implementer flagged them as intentional with rationale. This gate prevents implementers from rebuilding screens from textual specs and silently diverging from the approved visual. If no Comp is referenced, note it in the review but do not block.
- **Review packet path and digest** (paste the digest), and the instruction to invoke the `ai-tools:review` skill via the `Skill` tool with `PR #<PR>, base <milestone-branch>, packet <path>`. If the `Skill` tool can't resolve it in the subagent, the reviewer follows the [[review]] report shape manually — it does **not** re-fetch the diff via MCP
- **Token discipline** — the diff is in the packet (no `pull_request_read` for it); `CONTEXT.md`, the issue body, and the ADRs are in this brief (no re-reading from disk); implementing files are read in ranges around hunks, never whole unless the PR created the file
- **Output expectations** — the [[review]] report shape: Spec adherence / **Visual diff** (Comp vs. app — per screen, PASS or discrepancy list; omit this section if no Comp Reference exists) / Correctness & edge cases / Test coverage / **Vocabulary & domain alignment** / Migration safety if applicable / Idiom & style nits / Verdict, capped at ~400–500 words, ending in `verdict: approve | approve-with-nits | request-changes` and `posted: none`
- **Posting policy** — do NOT post review comments to Gitea. Findings come back to the main thread and the main thread decides what to act on. If anything is posted anyway, the `posted:` line must say what and where.

Run in the background and end the turn. When multiple PRs in this tier just hit green CI together, spawn all reviewers in one message. **Port note:** if multiple issues in the tier have `## Comp Reference`, each needs the app running from its own worktree. Start them on different ports and pass the correct URL to each reviewer brief. If port management is impractical, sequence the Visual diff gates instead of parallelizing them.

## Stage 4 — Apply review findings

When the reviewer reports back, key on its `verdict:` line (second-to-last line of the report; if missing or paraphrased, ask the reviewer for it). It is one of:

- **approve** → straight to Stage 5 for this PR
- **approve-with-nits** → fix the nits inline on the main thread (small mechanical edits in the implementer's worktree; commit + push). Then Stage 5.
- **request-changes** → a real bug, missed AC, Visual diff discrepancy, or vocabulary Blocker. Two paths:
  - **Inline fix** if the fix is under ~50 LOC and you have clear understanding from the review. Edit in the worktree, commit with a message like `fix(...): <one-line>. Reported by PR review on #<N>.`, push.
  - **Fix agent** (same model as the Implementer — see the Stage 1 example) for larger fixes or anything that needs to read significant repo state. Brief the agent with: the PR URL, the worktree path, the specific reviewer finding(s) to address, scope (do not expand beyond the finding), and reporting requirements (same gates as the original implementer).

When the reviewer flags a finding, **always check whether the implementer already flagged it as a known judgment call.** If yes, the question is whether the call was correct. Sometimes the reviewer is right (they have the actual diff; the implementer was reasoning from intent); sometimes they're missing why a parameter is reserved for an unmerged downstream issue. Decide on the main thread.

After a fix lands, re-review per [[review]]: re-spawn `review-prep` and a fresh reviewer briefed with the previous findings, asking only whether each is resolved (≤150 words). Delete the scratch dir once the PR merges.

## Stage 5 — CI gate (final pass) and merge

After any fix commits, recheck CI exactly as in Stage 2.

When CI is green, merge the PR into the milestone branch via Gitea MCP:

```
mcp__gitea__pull_request_write({
  method: "merge",
  owner: "<owner>",
  repo: "<repo>",
  index: <PR number>,
  merge_style: "<repo's standard — see MEMORY.md>",
  delete_branch: true,
})
```

Use the merge style the repo expects (squash on some repos, merge on others — read MEMORY.md). `Resolves #N` lives in the implementer's commit message so it propagates into the milestone branch and, eventually, into main — at which point Gitea auto-closes the issue. On squash-merge repos, make sure the squash commit message preserves `Resolves #N` rather than dropping it.

## Stage 6 — Update issue and clean up

Add a brief comment on the issue via Gitea MCP confirming the merge:

```
Implementation complete. PR #<PR-number> merged to milestone branch.
CI green, review approved.
```

Then return to the milestone orchestrator (SKILL.md step 4 / step 5) to pick up the next ready tier.

## Common failure modes

- **Implementer reports "tests pass" but skipped a separate lint gate.** For example, on Go repos where `gofmt` is a separate CI gate from `golangci-lint`, passing one doesn't imply the other. The implementer brief must enumerate every gate CI runs; check for it in the report-back.

- **Implementer's PR description includes Claude footers.** Many repos don't want them. The brief says no; agents sometimes default-include. Check and amend the PR body via `pull_request_write` `update` if needed.

- **Reviewer doesn't have the spec context** and produces a generic review. The reviewer brief must include the issue body and call out specific spec sections to scrutinize. Without these, reviews regress to "looks idiomatic, ship it" and miss real bugs.

- **`mergeable: false` after CI passes.** Almost always means Stage 0 was skipped or another PR merged into the milestone branch between Stage 0 and this PR's push. Recovery: into the implementer's worktree, `git fetch origin <milestone-branch>`, `git rebase origin/<milestone-branch>`, resolve conflicts, re-run all local gates, `git push --force-with-lease`. Wait for CI to re-green before merging.

- **Two parallel implementers from the same tier conflict on a shared file.** Sequence the merges. After the first merges, the second's worktree needs a rebase onto the new milestone-branch HEAD and a fresh push before CI will pass.

- **Reviewer requests changes on what's actually a design call.** Stop and surface to the user — the implementer made a defensible choice, the reviewer disagrees, the user arbitrates. Don't loop the Implementer on this.

- **Scope creep mid-implementation.** Implementer reports they want to expand beyond the issue body. Stop them — file a follow-up issue for the extra work and merge the originally-scoped PR.

- **Reviewer skips the Visual diff gate.** The review has no Visual diff section despite the issue having a Comp Reference. Send the reviewer back with explicit instructions to screenshot the running app and `Read` the Comp screenshots from the Design bundle to compare. This gate closes the design→code visual feedback loop — without it, the Comp is decoration, not a source of truth.
