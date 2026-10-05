# General-purpose skills

Skills that don't fit the language / plan / execute model — general-purpose utilities or domain-specific authoring helpers.

| Skill | Purpose |
|---|---|
| [`obsidian-note`](./obsidian-note/SKILL.md) | Create well-formatted markdown files for Obsidian with consistent frontmatter, structure, and wikilink conventions. |
| [`session-note`](./session-note/SKILL.md) | Capture an end-of-session summary of the current conversation as a dense Obsidian note. Opinionated about format and location; complements the structured `memory/` directory. |
| [`op-secrets`](./op-secrets/SKILL.md) | Use 1Password-stored credentials in commands without the secret value ever entering the conversation — `op run` with secret references (preferred, output-masked) or inline `$(op read ...)` capture. |
| [`har`](./har/SKILL.md) | Process browser HAR captures: sanitize secrets/PII (`scripts/sanitize-har.py`), verify, read in targeted digests (`scripts/har-digest.py`), isolate the real endpoint + write-only keys, extract fixtures, record in the observed-API doc. Never reads a raw HAR into the conversation. |
