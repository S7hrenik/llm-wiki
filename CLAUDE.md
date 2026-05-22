# CLAUDE.md — LLM Wiki Agent Schema

You are an agent that maintains a structured markdown knowledge base (the "wiki").
Your job is to synthesize knowledge at ingest time so queries can be answered from pre-compiled pages.

---

## Folder Layout

```
wiki/
├── index.md          # Master catalog of all wiki pages
├── log.md            # Chronological action log
├── overview.md       # High-level synthesis of all knowledge
├── sources/          # One page per ingested document
└── entities/         # One page per person, concept, or topic
raw/                  # Immutable source documents — never modify these
raw/assets/           # Downloaded images from URLs
```

---

## File Naming

- Source pages: `wiki/sources/<slug>.md` where slug is lowercase, hyphens, no spaces (e.g. `attention-is-all-you-need.md`)
- Entity pages: `wiki/entities/<slug>.md` (e.g. `transformer-architecture.md`, `geoffrey-hinton.md`)
- All filenames: lowercase, hyphens only, `.md` extension

---

## index.md Structure

```markdown
# Wiki Index

Last updated: YYYY-MM-DD HH:MM

## Sources
- [Title](sources/slug.md) — one-line description | ingested: YYYY-MM-DD

## Entities
- [Name](entities/slug.md) — one-line description | updated: YYYY-MM-DD
```

Always append new entries; never delete existing ones.

---

## log.md Structure

Each entry follows this format:

```markdown
## YYYY-MM-DD HH:MM — <ACTION>

- **Action:** INGEST | QUERY | LINT | UPDATE
- **Source:** filename or URL
- **Pages created:** list of new wiki pages
- **Pages updated:** list of modified wiki pages
- **Contradictions flagged:** list any conflicts found, or "none"
- **Notes:** brief free-text summary
```

Always prepend new entries (newest at top).

---

## Source Page Structure (`wiki/sources/<slug>.md`)

```markdown
---
title: <document title>
source: <filename or URL>
ingested: YYYY-MM-DD
tags: [tag1, tag2]
---

# <Title>

## Summary
2–4 sentence synthesis of the document's core argument or content.

## Key Takeaways
- Bullet point list of the most important facts, claims, or findings

## Key Entities
Links to entity pages: [[entity-name]], [[another-entity]]

## Contradictions
List any conflicts with existing wiki pages, or "None found."

## Raw Excerpt
Optional: short verbatim quote if highly significant
```

---

## Entity Page Structure (`wiki/entities/<slug>.md`)

```markdown
---
name: <entity name>
type: person | concept | tool | organization | event
updated: YYYY-MM-DD
sources: [source-slug-1, source-slug-2]
---

# <Entity Name>

## Definition
1–2 sentence definition or description.

## Key Facts
- Bullet list of important facts, accumulated across all sources

## Relationships
- Related to: [[other-entity]], [[another-entity]]
- Part of: [[parent-concept]]

## Source References
- [Source Title](../sources/slug.md) — what this source says about this entity

## Contradictions
Any conflicting information across sources, with citations.
```

When updating an entity page after a new ingest:
1. Add new facts to "Key Facts" (do not duplicate)
2. Add the new source to "Source References"
3. Update "Contradictions" if conflicts exist
4. Update the `updated` front matter date

---

## overview.md Structure

```markdown
# Knowledge Base Overview

Last updated: YYYY-MM-DD

## Themes
High-level themes across all ingested knowledge.

## Key Entities
The most important entities in this wiki, with brief descriptions.

## Open Questions
Gaps, contradictions, or areas needing more sources.
```

Regenerate this page after every 5th ingest or when explicitly asked.

---

## Contradiction Handling

When a new source conflicts with existing wiki content:
1. Note it in the source page under "Contradictions"
2. Note it in the affected entity page under "Contradictions"
3. Log it in `log.md`
4. Do NOT silently overwrite existing facts — preserve both versions with citations

---

## Cross-Referencing Rules

- Always link entity names using `[[entity-slug]]` syntax within page bodies
- Every entity page must list all sources that reference it
- Every source page must list all entity pages it touches
- `index.md` is the single source of truth for what exists in the wiki

---

## Token Budget — Query Mode

When answering a query, read in this order to stay within context limits:
1. `wiki/index.md` — find relevant pages (always read first)
2. Top 3 most relevant entity pages
3. Top 2 most relevant source pages
4. `wiki/overview.md` — only if needed for broad context

Stop reading once you have enough to synthesize a confident answer.

---

## Ingest Checklist

After ingesting a document, confirm you have:
- [ ] Created `wiki/sources/<slug>.md`
- [ ] Updated `wiki/index.md` (sources section)
- [ ] Created or updated 5–15 entity pages
- [ ] Flagged any contradictions
- [ ] Appended entry to `wiki/log.md`
- [ ] Updated `wiki/overview.md` if this is the 5th ingest or a major topic shift
