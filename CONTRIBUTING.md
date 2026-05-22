# Contributing to LLM Wiki Agent

Thanks for your interest in contributing!

## Setup

```bash
git clone https://github.com/S7hrenik/llm-wiki
cd llm-wiki
pip install anthropic rich pytest ruff black
```

Create a `.env` with your API key:

```
ANTHROPIC_API_KEY=sk-ant-...
```

## Running Tests

```bash
python -m pytest tests/ -v
```

Tests are fully mocked — no API calls are made.

## Code Style

```bash
ruff check .
black --check .
```

Fix issues with:

```bash
ruff check . --fix
black .
```

## Submitting a PR

1. Fork the repo and create a branch from `main`
2. Make your changes
3. Ensure all tests pass and linting is clean
4. Open a pull request with a clear description of what you changed and why

## Reporting Bugs

Open an issue with:
- What you ran
- What you expected
- What actually happened
- Your Python version and OS

## Feature Requests

Open an issue describing the use case. Features that fit the core principle — *knowledge synthesized at ingest time* — are most likely to be accepted.
