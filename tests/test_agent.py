"""Tests for llm-wiki agent commands (no API calls — mocked)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
import agent


@pytest.fixture(autouse=True)
def tmp_wiki(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(agent, "WIKI_DIR", tmp_path / "wiki")
    monkeypatch.setattr(agent, "RAW_DIR", tmp_path / "raw")
    monkeypatch.setattr(agent, "INDEX", tmp_path / "wiki" / "index.md")
    monkeypatch.setattr(agent, "LOG", tmp_path / "wiki" / "log.md")
    monkeypatch.setattr(agent, "OVERVIEW", tmp_path / "wiki" / "overview.md")
    monkeypatch.setattr(agent, "CLAUDE_MD", tmp_path / "CLAUDE.md")
    return tmp_path


# ── init ──────────────────────────────────────────────────────────────────────


def test_init_creates_files(tmp_wiki):
    agent.cmd_init()
    assert (tmp_wiki / "wiki" / "index.md").exists()
    assert (tmp_wiki / "wiki" / "log.md").exists()
    assert (tmp_wiki / "wiki" / "overview.md").exists()
    assert (tmp_wiki / "wiki" / "entities").is_dir()
    assert (tmp_wiki / "wiki" / "sources").is_dir()
    assert (tmp_wiki / "raw").is_dir()


def test_init_idempotent(tmp_wiki, capsys):
    agent.cmd_init()
    agent.cmd_init()
    # rich prints to its own console — just check it doesn't crash


# ── status ────────────────────────────────────────────────────────────────────


def test_status_not_initialized(tmp_wiki):
    agent.cmd_status()  # should not crash, prints "not initialized"


def test_status_after_init(tmp_wiki):
    agent.cmd_init()
    agent.cmd_status()


# ── ingest (mocked Claude) ────────────────────────────────────────────────────


MOCK_INGEST_RESPONSE = """\
===SOURCE_PAGE===
---
title: Test Doc
source: test.txt
ingested: 2026-01-01
tags: [test]
---

# Test Doc

## Summary
A test document for unit testing.

## Key Takeaways
- Takeaway one

## Key Entities
[[test-concept]]

## Contradictions
None found.

===ENTITY_PAGES===
---FILE: wiki/entities/test-concept.md---
---
name: Test Concept
type: concept
updated: 2026-01-01
sources: [test-doc]
---

# Test Concept

## Definition
A concept used for testing.

## Key Facts
- It is used in tests

===INDEX_UPDATE===
# Wiki Index

Last updated: 2026-01-01 00:00

## Sources
- [Test Doc](sources/test-doc.md) — a test document | ingested: 2026-01-01

## Entities
- [Test Concept](entities/test-concept.md) — a concept | updated: 2026-01-01

===LOG_ENTRY===
## 2026-01-01 00:00 — INGEST

- **Action:** INGEST
- **Source:** test.txt
- **Pages created:** wiki/sources/test-doc.md
- **Contradictions flagged:** none
"""


def test_ingest_file(tmp_wiki):
    agent.cmd_init()
    src = tmp_wiki / "test.txt"
    src.write_text("This is a test document about test concepts.", encoding="utf-8")

    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=MOCK_INGEST_RESPONSE)]
    )

    with patch("agent.get_client", return_value=mock_client):
        agent.cmd_ingest(source=str(src))

    assert (tmp_wiki / "wiki" / "entities" / "test-concept.md").exists()


# ── query (mocked Claude) ─────────────────────────────────────────────────────


def test_query_returns_answer(tmp_wiki, capsys):
    agent.cmd_init()

    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="The answer is 42, per wiki/entities/test.md.")]
    )

    with (
        patch("agent.get_client", return_value=mock_client),
        patch("agent.Confirm.ask", return_value=False),
    ):
        agent.cmd_query(question="What is the answer?")


# ── lint (mocked Claude) ──────────────────────────────────────────────────────


def test_lint_empty_wiki(tmp_wiki):
    agent.cmd_lint()  # no wiki dir → should print "empty" without crashing


def test_lint_with_content(tmp_wiki):
    agent.cmd_init()
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Wiki is healthy.")]
    )
    with patch("agent.get_client", return_value=mock_client):
        agent.cmd_lint()


# ── helpers ───────────────────────────────────────────────────────────────────


def test_slugify():
    assert agent._slugify("Hello World.pdf") == "hello-world"
    assert agent._slugify("Attention Is All You Need") == "attention-is-all-you-need"
    assert agent._slugify("test_file.txt") == "test-file"
