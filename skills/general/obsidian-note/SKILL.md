---
name: obsidian-note
description: "Create well-formatted markdown notes for Obsidian. Use when the user asks to create an Obsidian note, markdown file for notes, turn information into a note, document something for their notes, or references their Obsidian vault. Triggers include 'create an Obsidian note', 'make a markdown file for my notes', 'turn this into a note', 'add to my notes', or 'document this'. Do NOT use for end-of-session conversation summaries — that's /session-note."
---

# Obsidian Note Creator

Create markdown files formatted for Obsidian with consistent structure, frontmatter, and styling.

## File Naming

- Use spaces in filenames (e.g., `CloudNativePG SSL Configuration.md`)
- The filename IS the top-level header — Obsidian displays it as `#`
- Never include a `#` heading in the file content itself

## Document Structure

```markdown
---
tags:
  - tag1
  - tag2
created: YYYY-MM-DD
aliases:
  - Alternative Name
source: https://original-url-if-applicable.com
---

## First Section

Content starts at `##` level since filename serves as `#`.
```

## Frontmatter Fields

| Field | Required | Usage |
|-------|----------|-------|
| `tags` | Always | Categorization. Infer from content (e.g., `go`, `kubernetes`, `security`) |
| `created` | Always | Current date in `YYYY-MM-DD` format |
| `aliases` | Always | Alternative names for linking. Include abbreviations, alternate phrasings |
| `source` | If applicable | Original URL if note derives from a web resource. Omit field entirely if no source |

## Formatting Guidelines

### Callouts

Use Obsidian callout syntax for emphasis:

```markdown
> [!tip] Optional Title
> Helpful information or best practices

> [!warning] Optional Title
> Cautions or common pitfalls

> [!note] Optional Title
> Additional context or clarification

> [!info] Optional Title
> Background information

> [!danger] Optional Title
> Critical warnings or risks
```

Select the callout type that best fits the content's intent.

### Code Blocks

Always specify language for syntax highlighting:

````markdown
```go
func main() {}
```

```sql
SELECT * FROM users;
```

```bash
kubectl get pods
```
````

### Tables

Use for comparisons, option matrices, or structured reference data:

```markdown
| Option | Pros | Cons |
|--------|------|------|
| A | Fast | Complex |
| B | Simple | Slower |
```

### Wikilinks

Link to other notes when referencing concepts that likely have existing notes:

```markdown
See [[Kubernetes]] for cluster setup.
Related: [[PostgreSQL]], [[Docker]]
```

Use judgment — link concepts that seem like standalone note topics.

## Sources & Further Reading

Always include this section at the end when sources exist. Organize by category:

```markdown
## Sources & Further Reading

### Official Documentation
- [Resource Name](https://url) — Brief description

### Community Resources  
- [Resource Name](https://url) — Brief description

### Tools
- [Resource Name](https://url) — Brief description
```

Omit empty categories. Prioritize official docs, then authoritative community sources.

## Content Style

- Write in clear, direct prose
- Use bullet points sparingly — prefer flowing text for explanations, but keep it tight: most notes should land under ~400 words of prose (code blocks and tables don't count). Density beats coverage; cut background the reader can get from the linked sources
- Include practical examples and code snippets
- Start with a brief overview (2–3 sentences) before diving into details
- For ELI5/concept explanations: lead with the simple analogy, then expand with technical detail
