---
name: milestone-builder
description: "Implement Gitea issues by milestone with dependency-aware ordering, testing, and PR creation, using a parallel-agent flow that keeps the Main thread on judgment work and dispatches execution to subagents (role→model mapping in MODELS.md). Takes a milestone, fetches all its issues, parses dependencies, and works through them in topological order — spawning Implementer, Reviewer, and Fix-agent subagents per issue, with CI gates between stages, until the milestone is complete. MANDATORY TRIGGERS: implement milestone, build milestone, work on milestone, build phase, implement phase, start building, pick up issues, work through issues, churn out issues."
---

# Milestone Builder

Orchestrate implementation of an entire milestone's issues in dependency order, dispatching implementation to Implementer subagents and review to Reviewer subagents so the main thread stays on judgment work and its context stays lean.

## Philosophy

- **Dependency order is law** — never start an issue whose blockers are still open
- **Each issue is atomic** — branch, implement, review, fix, PR-merge, then move on
- **Validate before advancing** — CI must be green before review; review must clear before merge
- **UJTs are the acceptance contract** — if the issue body lists `## UJTs to Translate`, the implementer translates each to a runnable test (XCUITest, Playwright, etc.) in the same PR, and the PR is not done until they pass. UJT failures that look like design-vs-code drift get triaged on the main thread (see Stage 2.5 in the implementation workflow); skip-triage merges are the bug this loop exists to prevent.
- **Tiered branching** — main → milestone branch → issue branches; issues merge into the milestone branch, main stays clean until user review
- **Use Gitea MCP for all issue operations** — not tea CLI, not markdown files
- **Play each model to its strengths** — the judgment model for cross-issue context, arbitration, and review; the execution model for well-specified implementation (see Model split)

## Model split — why this flow uses two model tiers

The flow splits roles across model tiers: a judgment model thinks and arbitrates, an execution model types. The current role→model mapping — and the capability rationale behind it — lives in `MODELS.md` at the repo root; change it there first when models churn. The shape below survives any particular mapping:

- **Main thread — orchestrator and arbiter, on the judgment model.** Holding the milestone's dependency graph, the cached issue bodies, the in-flight branches, and the cross-issue integration risks in mind at once. Briefing implementers, briefing reviewers, arbitrating reviewer findings against implementer judgment calls, deciding when to merge each issue PR, and deciding when the milestone is done. This is exactly the long-context, cross-cutting reasoning the strongest judgment model is for. Do not downgrade the main thread — you would lose the very thing that makes the milestone-wide view coherent. (Skills can't set the session model; the user picks it via `/model`.)
- **Implementer subagents — execution.** The Implementer does its best work when the brief is concrete: read-list spelled out, scope locked, repo conventions named, edge cases pre-resolved. The brief should let the implementer move fast and write idiomatic code without burning tokens deliberating design. If you find yourself writing "use your judgment on X" in an implementer brief, stop and decide X on the main thread first — that's a Main-thread judgment task masquerading as execution.
- **Reviewer subagents — judgment.** Review is what the strongest model is for: spec adherence, design soundness, hidden-state risk, missing test coverage, whether a flagged judgment call holds up against the actual diff. Weaker reviewers tend to pattern-match toward "approve" and miss subtle bugs — never run the Reviewer on a weaker model than the Implementer.
- **Fix subagents — execution, second pass.** For real bugs flagged by the reviewer, brief a Fix agent the same way as the original implementer: concrete scope (the specific finding), no design latitude.
- **Inline fixes on the main thread.** Trivial mechanical fixes (lint nits, dead-code removal, doc typos, formatting) — edit in the worktree directly. A Fix agent's per-spawn startup cost beats the fix size when the change is under roughly 50 LOC.

The implicit contract: **the judgment model thinks, the execution model types**. When that contract slips — the Implementer is making design calls, or the Main thread is dispatching trivial edits to a subagent — the flow loses its edge.

## Startup

When triggered, gather:

1. **Repository** — check `git remote -v` for owner/repo, confirm with user
2. **Milestone** — ask which milestone to implement (list available via MCP if needed)
3. **MCP verification** — test with a read operation (list issues) to confirm access
4. **Memory scan** — read `MEMORY.md` and the linked files for repo conventions that change implementer/reviewer briefs (merge style, CI gates not in workflow files, branch naming, commit style, footer rules)

Then read the project's `CLAUDE.md` for tech stack, conventions, and project structure. **Also read `CONTEXT.md` (the domain glossary) and any ADRs in `docs/adr/` that touch the milestone's area**. Keep all this content in the main thread so each subagent brief can quote what it needs without the subagent re-reading the whole project.

If `CONTEXT.md` does not exist in the repo, stop and surface that to the user — a milestone-scale build with no shared vocabulary will compound vocabulary drift across the parallel implementers. Offer to run `/grill-with-docs` to seed `CONTEXT.md` from the existing code and the milestone's issues before starting. See [[grill-with-docs]].

## Triage gate

This skill expects every issue in the milestone to be in `ready-for-agent`. If any milestone issue is still `needs-triage` or `needs-info`, **stop and refuse to start** — surface the offending issues and route them through [[triage]] first. Spawning Implementers against under-briefed issues is the failure mode that compounds across a milestone-scale build.

## Branching Strategy

```
main
 └── milestone-<ID>-<kebab-name>          (created at startup)
      ├── issue-<N>-<short-description>   (PR targets milestone branch)
      ├── issue-<M>-<short-description>
      └── ...
```

- **Milestone branch** — created from main at the start. All issue PRs target this branch and are merged after CI and review pass.
- **Issue branches** — created in Implementer worktrees from the milestone branch. Worktrees inherit local HEAD, so the milestone branch must be synced before each tier (see the per-issue workflow's Stage 0). Each branch gets its own PR targeting the milestone branch.
- **Final PR** — when all issues are complete, a single PR from the milestone branch → main is created and left **open** for user review.
- **Issue closure** — issue PRs use `References #N` (not `Closes`). Commits use `Resolves #N`, which auto-closes issues only when the milestone PR merges those commits into main.

## Workflow

### 1. Create Milestone Branch

```bash
git checkout main && git pull
git checkout -b milestone-<ID>-<kebab-name>
git push -u origin milestone-<ID>-<kebab-name>
```

### 2. Fetch and Parse

The Gitea MCP has no milestone filter on `list_issues`. Use this sequence:

1. **Get the milestone ID** — call `milestone_read` (method `list`) to find the target milestone and note its `id` and `open_issues` count
2. **List all open issues** — call `list_issues` (state `open`, perPage `50`, paginate as needed) to get all open issue numbers
3. **Read each issue** — call `issue_read` (method `get`) on each issue number. Check `milestone.id` against the target. Collect matching issues. Stop early once you've found the expected `open_issues` count.
4. **Parse dependencies** — for each matching issue, parse the `## Dependencies` section:

```
**Blocked by:** #7, #15
**Blocks:** #22, #29
```

Extract blocked-by issue numbers and build an adjacency list for topological ordering. If an issue has no Dependencies section, treat it as having no blockers.

**Cache the full issue bodies on the main thread** — every implementer and reviewer brief will need them, and re-reading via MCP per agent burns tokens for no reason. On a large milestone, cache the brief-relevant sections (description, AC, technical notes, UJT list, dependencies) rather than every word — the main thread's context is the scarcest resource in the flow.

### 3. Compute Execution Order

Sort issues topologically:
- An issue is **ready** when none of its blockers are open (including issues with no blockers at all)
- Process ready issues in dependency tiers — every issue in a tier can run in parallel
- After a tier completes, re-evaluate which issues become ready

### 4. Implement Each Tier

For every ready issue in the current tier, run the per-issue agent flow described in [references/implementation-workflow.md](references/implementation-workflow.md).

**Parallelism is the whole point.** When a tier has multiple ready issues, spawn the Implementers in a single turn (multiple `Agent` tool calls in the same message). Same for reviewers when their PRs hit CI-green. Sequential dispatch throws away the largest wall-clock win.

Watch for **shared-file conflicts** between parallel branches. Common culprits: `internal/config/config.go`, top-level `Makefile`, schema files, route registries. If two ready issues touch the same file, sequence them instead of paralleling — the second one will need a rebase before merge either way, and parallel work just wastes the rebase.

### 5. Milestone Completion

When all issues are implemented and merged into the milestone branch:
1. Run a full validation pass on the milestone branch (lint, tests, build — same gates CI runs)
2. Flag any cross-issue integration problems and fix them. For non-trivial integration bugs, file a new issue under the milestone and ship it through the same flow rather than smuggling a fix into an unrelated branch.
3. Create a PR from the milestone branch → main via Gitea MCP, left **open** for user review
4. Report final status with the milestone PR link and a summary of all issues implemented

The milestone PR body lists all implemented issues for context. Do not use `Closes` keywords in the PR body — the `Resolves #N` in individual commits will auto-close issues when the PR merges into main.

## Resuming a Milestone

If a conversation ends mid-milestone, on resume:
1. Check which issue branches already have merged PRs in the milestone branch — those issues are done
2. Check for in-progress work — local worktrees (`git worktree list`), unpushed commits, open PRs awaiting CI/review/merge. Assess whether to continue or restart.
3. Re-run the topological sort on remaining open issues
4. Continue from the next ready tier (or resume the in-progress issue at whichever stage it's in)

## Error Recovery

**Test or lint failures inside an issue:** the implementer or fix agent fixes them within that issue's branch. Do not skip to the next issue.

**Pre-existing failures:** if validation fails due to a problem that existed before the current issue (e.g., a broken config file, a flaky test unrelated to the current work), do not fix it in the current issue's branch. Instead:
1. Create a new issue via Gitea MCP describing the pre-existing problem
2. Label it appropriately (e.g., `priority:high`, `type:bug`)
3. Add it to the current milestone
4. Implement it as its own issue — branch, fix, PR, CI, review, merge — before continuing with the blocked issue

This keeps each issue's scope clean and creates traceability for the fix.

**Merge conflicts:** rebase the feature branch on the milestone branch from inside the worktree. If conflicts are non-trivial, stop and report to user.

**Blocked issue discovered mid-implementation:** if an implementer reports a dependency not captured in the issue body, stop, report the discovery, and ask whether to add the dependency or proceed.

**Implementation unclear:** if an issue's description or technical notes are insufficient for a concrete implementer brief, stop and ask the user rather than spawning an under-briefed agent. An under-briefed Implementer costs more than the clarifying question.

**Main branch drift:** if main advances during the milestone, rebase the milestone branch on main before starting the next dependency tier to avoid a painful final merge.

**Reviewer flags something the implementer already noted as a judgment call:** the question is whether the call was correct. Sometimes the reviewer is right (they have the actual diff; the implementer was reasoning from intent). Decide on the main thread; don't reflexively forward.

## When to Check In

- **Before starting a new milestone** — confirm the target
- **After completing all issues in a dependency tier** — brief progress update
- **On any error that can't be auto-resolved** — implementer fails twice on the same issue, merge conflicts, missing dependencies
- **On reviewer/implementer disagreement that's a design call** — surface to user for arbitration
- **On scope creep** — an implementer reports they want to expand the scope beyond the issue body
- **At milestone completion** — full status report with the milestone PR link

Do NOT check in after every individual issue. The goal is autonomous progress at the milestone level.

## References

| Reference | When to Read |
|-----------|-------------|
| [references/implementation-workflow.md](references/implementation-workflow.md) | Before implementing the first issue in a milestone — detailed per-issue agent flow, briefs, and gates |
