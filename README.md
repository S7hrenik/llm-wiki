# 🧠 LLM Wiki Agent

> An open-source CLI that turns Claude into a self-maintaining knowledge base.  
> Knowledge is **synthesized at ingest time** — not rediscovered on every query.

[![CI](https://github.com/S7hrenik/llm-wiki/actions/workflows/ci.yml/badge.svg)](https://github.com/S7hrenik/llm-wiki/actions/workflows/ci.yml)
[![Lint](https://github.com/S7hrenik/llm-wiki/actions/workflows/lint.yml/badge.svg)](https://github.com/S7hrenik/llm-wiki/actions/workflows/lint.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![PyPI](https://img.shields.io/pypi/v/llm-wikibase)](https://pypi.org/project/llm-wikibase/)

---

## The Idea

Most RAG systems make the LLM do all the heavy lifting at query time — searching raw docs and synthesizing answers from scratch on every request.

LLM Wiki flips this: **Claude reads and synthesizes your documents when you add them**, compiling structured markdown pages. When you ask a question, Claude reads pre-built wiki pages — not raw source text.

```
Basic RAG   →  question → search raw docs → LLM answers from scratch (every time)
LLM Wiki    →  ingest doc → Claude compiles wiki → question → Claude reads wiki
```

The wiki grows smarter with every document added. Contradictions are flagged. Entities are cross-referenced. Knowledge compounds.

---

## Architecture

```
llm-wiki/
├── CLAUDE.md              ← Agent instructions: how to maintain the wiki
├── agent.py               ← CLI entrypoint (interactive TUI)
│
├── raw/                   ← Your source documents (immutable, never modified)
│   └── assets/            ← Downloaded images
│
└── wiki/                  ← LLM-generated knowledge base
    ├── index.md           ← Catalog of all pages
    ├── log.md             ← Chronological action log
    ├── overview.md        ← High-level synthesis across all sources
    ├── sources/           ← One summary page per ingested document
    └── entities/          ← One page per person, concept, tool, or topic
```

### Three Layers

| Layer | What It Is | Who Owns It |
|---|---|---|
| **Raw sources** | Documents, articles, text files — immutable source of truth | You |
| **The wiki** | Synthesized markdown: summaries, entity pages, index, log | Claude |
| **The schema** | `CLAUDE.md` — instructions for how Claude maintains the wiki | Both |

---

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)

---

## Install

```bash
pip install llm-wikibase
```

Set your API key — create a `.env` file in your working directory:

```
ANTHROPIC_API_KEY=sk-ant-...
```

> **Windows users:** If `llm-wikibase` is not recognized after install, run this once in PowerShell:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```
> Then open a new terminal.

**Or run from source:**

```bash
git clone https://github.com/S7hrenik/llm-wiki
cd llm-wiki
pip install anthropic rich
python agent.py
```

---

## Quick Start

```bash
python agent.py
```

You'll land in an interactive menu:

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║   ██╗     ██╗     ███╗   ███╗    ██╗    ██╗██╗██╗  ██╗██╗          ║
║   ██║     ██║     ████╗ ████║    ██║    ██║██║██║ ██╔╝██║          ║
║   ██║     ██║     ██╔████╔██║    ██║ █╗ ██║██║█████╔╝ ██║          ║
║   ...                                                                ║
║      Knowledge synthesized at ingest time — not on every query      ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

  [1]  🚀  Init     Bootstrap a new wiki
  [2]  📥  Ingest   Add a document or URL to the wiki
  [3]  🔍  Query    Ask a question, get a cited answer
  [4]  🔧  Lint     Health-check for gaps & contradictions
  [5]  📊  Status   Wiki stats at a glance
  [0]  👋  Exit
```

### Step-by-step

**1. Init** — bootstrap the wiki (run once):
```
Choose: 1
```

**2. Ingest** — add a document or URL:
```
Choose: 2
File path or URL: raw/my-paper.md
```
Claude creates a source summary page, extracts 5–15 entity pages, updates the index, and logs the action.

**3. Query** — ask anything:
```
Choose: 3
Your question: What are the key contributions of the Transformer architecture?
```
Claude reads the pre-compiled wiki and responds with citations to specific pages.

**4. Lint** — audit the wiki for contradictions, broken links, and gaps:
```
Choose: 4
```

**5. Status** — quick stats at a glance:
```
Choose: 5

  📄  Source pages   3
  🏷️   Entity pages   27
  🕐  Last ingest    2026-05-22 20:09
  📁  Wiki dir       /home/user/my-wiki/wiki
```

---

## How It Works

### Ingest Flow

When you run **Ingest** on a document:

1. Claude reads the full source document
2. Writes a **source summary page** to `wiki/sources/<slug>.md`
3. Creates or updates **5–15 entity pages** in `wiki/entities/` (people, concepts, tools, organizations)
4. Updates `wiki/index.md` with the new entries
5. Flags any **contradictions** with existing pages
6. Appends a timestamped entry to `wiki/log.md`

### Query Flow

When you run **Query**:

1. Claude reads `wiki/index.md` to find relevant pages
2. Drills into the most relevant entity and source pages
3. Synthesizes a cited answer — every fact links back to the wiki page it came from
4. Optionally saves the answer as a new wiki page (explorations compound)

### Lint

Audits the entire wiki for:
- Contradictions between pages
- Orphaned pages not referenced in `index.md`
- Entities mentioned but missing their own page
- Stale or incomplete pages
- Cross-reference gaps

---

## Tech Stack

| Tool | Purpose |
|---|---|
| [Claude](https://anthropic.com) (`claude-sonnet-4-6`) | The brain — reads, writes, synthesizes the wiki |
| [Anthropic Python SDK](https://github.com/anthropics/anthropic-sdk-python) | API wrapper |
| [Rich](https://github.com/Textualize/rich) | Terminal UI — panels, spinners, color |
| Python 3.10+ | CLI orchestration, file I/O |
| Markdown files | The wiki itself — plain text, git-trackable |
| GitHub Actions | CI/CD: tests, linting, PyPI publish |

---

## CLAUDE.md — The Schema

`CLAUDE.md` is the agent's operating manual. It defines:

- Folder layout and file naming conventions
- How `index.md` and `log.md` are structured
- Entity page format (front matter, sections, contradiction flags)
- Cross-referencing rules between pages
- Contradiction handling (never silently overwrite — preserve both versions with citations)
- Token budget hints for query mode (which files to read first)

You can edit `CLAUDE.md` to customize how the wiki behaves for your domain.

---

## GitHub Actions

| Workflow | Trigger | What It Does |
|---|---|---|
| `ci.yml` | Every PR and push to `main` | Runs pytest on Python 3.10, 3.11, 3.12 |
| `lint.yml` | Every PR | Runs ruff + black check |
| `publish.yml` | New GitHub release tag | Auto-builds and publishes to PyPI |

All PRs must pass CI and Lint before merging into `main`.

---

## Contributing

Pull requests are welcome. For major changes, open an issue first.

```bash
git clone https://github.com/S7hrenik/llm-wiki
cd llm-wiki
pip install anthropic rich pytest ruff black
python -m pytest tests/
```

Make sure `ruff check .` and `black --check .` pass before submitting.  
All changes go through a branch → PR → checks green → merge workflow.

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

---

## License

[MIT](LICENSE)

---

*Built with [Claude](https://anthropic.com) by [Shrenik Purvant](https://github.com/S7hrenik)*
