---
name: session-note
description: "Capture a dense end-of-session summary of the current Claude Code conversation as a markdown note in the user's Obsidian vault — what was decided, why, what was built, what's still pending, and the load-bearing paths. Use when the user asks to save/file/record a session note, summarize this conversation, capture what we did today, write up this session for my notes, document this conversation, or end-of-session memory. Triggers include 'save this as a session note', 'write up what we did', 'capture this conversation', 'file a session note', 'remember this session', 'session summary for Obsidian', 'end-of-session note'. Not for atomic facts (those go in the auto-memory memory/ directory) or for general note-taking (use /obsidian-note for that). Designed to be invoked manually at the end of meaningful sessions — not every chat warrants a permanent note."
---

# Session Note

Distill the current Claude Code conversation into a single, dense Obsidian note that a future session — or a future human — can pick up cold. This is the **session-summary** layer that complements the structured `memory/` directory: `memory/` holds atomic facts, session notes hold the rationale, the failed attempts, and the load-bearing paths.

## When to invoke

Use when **all** of these hold:
- The session produced a non-trivial decision, artifact, or diagnosis worth preserving.
- The information would not be easy to reconstruct from `git log` or the codebase alone — there's *why* and *what-we-ruled-out* that lives only in the conversation.
- The user asks for it explicitly, or you're at a natural session boundary (a milestone shipped, a multi-hour design session wrapped, a hard bug got root-caused) and you're proactively offering.

Do **not** use for:
- Routine implementation sessions where the diff and PR description capture everything important.
- Atomic facts about the user or the project — those belong in the auto-memory `memory/` directory.
- General-purpose note creation — use `/obsidian-note` for that (this skill is opinionated about format and location).

## Naming convention

Filename: `YYYY-MM-DD - <Topic Title>.md`

- **Date**: ISO date of the session (today, when filing). If the session spanned multiple days, use the start date.
- **Topic Title**: Title Case, concise, names the *artifact* or *decision*, not the activity.
  - ✅ `2026-05-26 - Skill Set Redesign.md`
  - ✅ `2026-05-26 - Billing Service Issue 57 Retry Backoff.md`
  - ❌ `2026-05-26 - Worked on the Skill Set.md` (activity, not artifact)
  - ❌ `2026-05-26 - Misc Notes.md` (no thing named)
- **Disambiguation**: same-day collision → append ` (2)`, ` (3)`. Rare.

Location: the user's session-note folder, found in this order:

1. The `SESSION_NOTE_DIR` environment variable (check with `printenv SESSION_NOTE_DIR`).
2. A line in the user's `CLAUDE.md` (user-level or project) of the form `Session notes: <path>`.
3. Neither set → ask the user where session notes go. Offer to add the `Session notes: <path>` line to their user-level `CLAUDE.md` so the next session finds it; don't guess a vault path.

## Document shape

Match the format of any notes already in that folder.

### Frontmatter

```yaml
---
tags:
  - chat-history
  - memory
  - <project-name>
  - <one-or-two-topic-tags>
created: YYYY-MM-DD
aliases:
  - <2–4 short search-friendly aliases>
---
```

- `chat-history` and `memory` are always present.
- Add one project tag (e.g. `ai-tools`, `billing-service`) if the session was project-scoped.
- Add 1–3 topic tags (e.g. `workflow-design`, `diarization`, `plugin-distribution`).
- `aliases` are alternative names a future fuzzy search might land on — short noun phrases, not full sentences.

### Body

Lead with a dense **TLDR** (or **Why this work exists** for project-shaped sessions) — one or two paragraphs that capture the punchline before any detail. Someone skimming should be able to stop after the TLDR.

Then use themed H2 sections drawn from this menu — pick the ones that fit, in this rough order:

| Section | When to include |
|---|---|
| `## TLDR` or `## Why this work exists` | Always |
| `## Diagnosis` (what was wrong) | If session was rooted in a problem |
| `## Key decisions` (table: decision \| rationale) | If decisions were made worth defending later |
| `## What was built` | If artifacts shipped (code, docs, configs) |
| `## Key paths` (table: thing \| path) | If file/folder locations matter for future-you |
| `## Pending` or `## Pending action` | If the work isn't done |
| `## Signals that the discipline is working` | For convention/process changes |
| `## Diagnosis history` | If a wrong path was tried before the right one — capture it so the next person doesn't repeat it |
| `## Related notes` | Wikilinks to other vault notes |

Cross-link to other vault notes with `[[Note Name]]`. Cross-link to repos with full paths or GitHub URLs.

### Style

- **Dense, not exhaustive.** A session note is not a transcript. Cut anything that's only true for this exact session. As a hard ceiling, keep the whole note under ~500 words (tables count half) — if it's running longer, you're transcribing, not distilling; per-section, 2–5 rows or sentences is the norm.
- **Capture the *why*.** Decisions, ruled-out approaches, error messages that fooled you, surprising constraints. These are the things that decay from human memory and aren't in the git log.
- **Concrete paths and identifiers.** Hashes, file paths, issue numbers, exact error strings. Future-you will search for these.
- **Match the project's voice.** The existing session-note folder uses plain technical prose, em-dashes, occasional emphasis. Don't be cute.

## Procedure

1. **Confirm scope.** Ask the user one short question: what's the topic title? Offer 2–3 candidates based on the conversation. Skip this if the user already named the note.
2. **Pick the date.** Today's date (the date you have in context).
3. **Draft the body** from conversation context. Pull from the actual exchange — quote specific decisions, list the actual files touched, name the actual errors hit. Do not invent generic phrasing.
4. **Write the file** at the path above using the Write tool. Filename per the naming convention.
5. **Tell the user the full path** so they can open it in Obsidian.
6. **If a related note already exists** (check the session-note folder first), suggest updating it instead of creating a new one — long-running threads (e.g. an ongoing migration) belong in one growing note, not many fragmented ones.

## Heuristic for "is this worth a note?"

If you can answer yes to any:
- Did we hit a wrong answer that looked right and would fool the next person? → yes, write the diagnosis history.
- Did we make a decision a future-you would want to second-guess? → yes, capture the rationale.
- Did we set up infrastructure (plugin install, repo conventions, vault layout) that's load-bearing for future sessions? → yes, write the key-paths table.
- Did we just write some code that's now in git? → probably no — the diff and PR description are enough.

When in doubt, **skip the note**. The session-note folder's value comes from signal-to-noise. A folder full of trivial summaries is worse than a folder of a few high-signal ones.
