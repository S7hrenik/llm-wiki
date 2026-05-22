#!/usr/bin/env python3
"""LLM Wiki Agent — Interactive TUI powered by Claude."""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

import anthropic
from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

console = Console()

MODEL = "claude-sonnet-4-6"
WIKI_DIR = Path("wiki")
RAW_DIR = Path("raw")
INDEX = WIKI_DIR / "index.md"
LOG = WIKI_DIR / "log.md"
OVERVIEW = WIKI_DIR / "overview.md"
CLAUDE_MD = Path("CLAUDE.md")

# Load .env if present
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())


# ── Core helpers ─────────────────────────────────────────────────────────────


def get_client() -> anthropic.Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print("[bold red]Error:[/] ANTHROPIC_API_KEY not set. Add it to [cyan].env[/]")
        sys.exit(1)
    return anthropic.Anthropic(api_key=api_key)


def load_schema() -> str:
    return CLAUDE_MD.read_text(encoding="utf-8") if CLAUDE_MD.exists() else ""


def load_index() -> str:
    return INDEX.read_text(encoding="utf-8") if INDEX.exists() else ""


def call_claude(client: anthropic.Anthropic, system: str, user: str, spinner_msg: str = "Claude is thinking...") -> str:
    with console.status(f"[bold cyan]{spinner_msg}[/]", spinner="dots"):
        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    return response.content[0].text


def _slugify(text: str) -> str:
    text = Path(text).stem if "." in text else text
    text = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return text.strip("-")


def _gather_wiki_context(question: str, index_content: str) -> str:
    parts = [f"=== wiki/index.md ===\n{index_content}"]
    if OVERVIEW.exists():
        parts.append(f"=== wiki/overview.md ===\n{OVERVIEW.read_text(encoding='utf-8')}")
    budget = 40000 - len("\n".join(parts))
    for directory in [WIKI_DIR / "entities", WIKI_DIR / "sources"]:
        if not directory.exists():
            continue
        for md_file in sorted(directory.glob("*.md")):
            chunk = f"=== {md_file} ===\n{md_file.read_text(encoding='utf-8', errors='replace')}"
            if len(chunk) < budget:
                parts.append(chunk)
                budget -= len(chunk)
    return "\n\n".join(parts)


def _save_query_as_page(question: str, answer: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    out = WIKI_DIR / "sources" / f"query-{_slugify(question[:50])}.md"
    out.write_text(
        f"---\ntitle: Query — {question}\ntype: query\ndate: {now}\n---\n\n# {question}\n\n{answer}\n",
        encoding="utf-8",
    )
    return out


# ── Banner & menu ─────────────────────────────────────────────────────────────


def show_banner():
    console.clear()

    art = Text(justify="center")
    art.append("██╗     ██╗     ███╗   ███╗    ", style="bold bright_cyan")
    art.append("██╗    ██╗██╗██╗  ██╗██╗\n", style="bold white")
    art.append("██║     ██║     ████╗ ████║    ", style="bold bright_cyan")
    art.append("██║    ██║██║██║ ██╔╝██║\n", style="bold white")
    art.append("██║     ██║     ██╔████╔██║    ", style="bold bright_cyan")
    art.append("██║ █╗ ██║██║█████╔╝ ██║\n", style="bold white")
    art.append("██║     ██║     ██║╚██╔╝██║    ", style="bold bright_cyan")
    art.append("██║███╗██║██║██╔═██╗ ██║\n", style="bold white")
    art.append("███████╗███████╗██║ ╚═╝ ██║    ", style="bold bright_cyan")
    art.append("╚███╔███╔╝██║██║  ██╗██║\n", style="bold white")
    art.append("╚══════╝╚══════╝╚═╝     ╚═╝    ", style="bold bright_cyan")
    art.append("╚══╝╚══╝ ╚═╝╚═╝  ╚═╝╚═╝", style="bold white")

    tagline = Text(
        "\n  Knowledge synthesized at ingest time — not rediscovered on every query  ",
        style="italic dim white",
        justify="center",
    )

    console.print()
    console.print(Panel(
        Align.center(Text.assemble(art, tagline)),
        border_style="bright_cyan",
        box=box.DOUBLE_EDGE,
        padding=(1, 2),
    ))
    console.print()


def show_menu():
    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 3))
    table.add_column("key",  style="bold bright_cyan", no_wrap=True, width=5)
    table.add_column("icon", width=3)
    table.add_column("cmd",  style="bold white", width=10)
    table.add_column("desc", style="dim white")

    table.add_row("[1]", "🚀", "Init",   "Bootstrap a new wiki")
    table.add_row("[2]", "📥", "Ingest", "Add a document or URL to the wiki")
    table.add_row("[3]", "🔍", "Query",  "Ask a question, get a cited answer")
    table.add_row("[4]", "🔧", "Lint",   "Health-check for gaps & contradictions")
    table.add_row("[5]", "📊", "Status", "Wiki stats at a glance")
    table.add_row("",    "",   "",       "")
    table.add_row("[0]", "👋", "Exit",   "")

    console.print(Panel(
        Align.center(table),
        title="[bold bright_cyan]  MENU  [/]",
        border_style="cyan",
        box=box.ROUNDED,
    ))


# ── Commands ──────────────────────────────────────────────────────────────────


def cmd_init():
    console.print(Rule("[bold cyan]  Init  [/]", style="cyan"))

    if INDEX.exists():
        console.print("[yellow]Wiki already initialized.[/] Delete [cyan]wiki/[/] to start fresh.")
        return

    WIKI_DIR.mkdir(parents=True, exist_ok=True)
    (WIKI_DIR / "entities").mkdir(exist_ok=True)
    (WIKI_DIR / "sources").mkdir(exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / "assets").mkdir(exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    INDEX.write_text(f"# Wiki Index\n\nLast updated: {now}\n\n## Sources\n\n## Entities\n", encoding="utf-8")
    LOG.write_text(f"# Wiki Log\n\n## {now} — INIT\n\n- **Action:** INIT\n- **Notes:** Wiki initialized.\n", encoding="utf-8")
    OVERVIEW.write_text(
        f"# Knowledge Base Overview\n\nLast updated: {now}\n\n"
        "## Themes\n\n_No content yet._\n\n"
        "## Key Entities\n\n_No content yet._\n\n"
        "## Open Questions\n\n_No content yet._\n",
        encoding="utf-8",
    )

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    table.add_column("file", style="cyan")
    table.add_column("status", style="green")
    table.add_row(str(INDEX), "✅ created")
    table.add_row(str(LOG), "✅ created")
    table.add_row(str(OVERVIEW), "✅ created")

    console.print(Panel(table, title="[green]  Wiki Initialized  [/]", border_style="green"))


def cmd_ingest(source: str | None = None):
    console.print(Rule("[bold cyan]  Ingest  [/]", style="cyan"))

    if source is None:
        source = Prompt.ask("[cyan]File path or URL[/]").strip()

    client = get_client()
    schema = load_schema()
    index_content = load_index()

    if source.startswith(("http://", "https://")):
        with console.status("[cyan]Fetching URL...[/]", spinner="dots"):
            try:
                import urllib.request
                with urllib.request.urlopen(source) as resp:
                    raw_content = resp.read().decode("utf-8", errors="replace")
            except Exception as e:
                console.print(f"[red]Error fetching URL:[/] {e}")
                return
        source_label = source
    else:
        src_path = Path(source)
        if not src_path.exists():
            console.print(f"[red]File not found:[/] {source}")
            return
        raw_content = src_path.read_text(encoding="utf-8", errors="replace")
        source_label = src_path.name

    system = f"""You are an LLM Wiki Agent. Follow the schema defined in CLAUDE.md exactly.

<schema>
{schema}
</schema>

Current wiki index:
<index>
{index_content}
</index>

Respond in this exact format:

===SOURCE_PAGE===
<full markdown content of wiki/sources/<slug>.md>

===ENTITY_PAGES===
---FILE: wiki/entities/<slug>.md---
<full markdown content>

===INDEX_UPDATE===
<full updated wiki/index.md>

===LOG_ENTRY===
<just the new ## YYYY-MM-DD entry block>"""

    user = f"Ingest this document from '{source_label}':\n\n{raw_content[:20000]}"
    response = call_claude(client, system, user, f"Ingesting [bold]{source_label}[/]...")

    # Parse sections
    sections: dict[str, str] = {}
    current = None
    buf: list[str] = []
    for line in response.splitlines(keepends=True):
        tag = line.strip()
        if tag == "===SOURCE_PAGE===":
            current = "source"; buf = []
        elif tag == "===ENTITY_PAGES===":
            if current: sections[current] = "".join(buf)
            current = "entities"; buf = []
        elif tag == "===INDEX_UPDATE===":
            if current: sections[current] = "".join(buf)
            current = "index"; buf = []
        elif tag == "===LOG_ENTRY===":
            if current: sections[current] = "".join(buf)
            current = "log"; buf = []
        else:
            buf.append(line)
    if current:
        sections[current] = "".join(buf)

    created: list[tuple[str, str]] = []

    source_block = sections.get("source", "").strip()
    if source_block:
        m = re.search(r"wiki/sources/([^\s]+\.md)", source_block)
        slug = m.group(1) if m else _slugify(source_label) + ".md"
        out = WIKI_DIR / "sources" / slug
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(source_block, encoding="utf-8")
        created.append((str(out), "source page"))

    entities_block = sections.get("entities", "")
    for m in re.finditer(r"---FILE: (wiki/entities/[^\n]+\.md)---\n(.*?)(?=---FILE:|$)", entities_block, re.DOTALL):
        fp = Path(m.group(1).strip())
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(m.group(2).strip(), encoding="utf-8")
        created.append((str(fp), "entity"))

    index_block = sections.get("index", "").strip()
    if index_block:
        INDEX.write_text(index_block, encoding="utf-8")
        created.append((str(INDEX), "index"))

    log_entry = sections.get("log", "").strip()
    if log_entry and LOG.exists():
        existing = LOG.read_text(encoding="utf-8")
        lines = existing.split("\n", 1)
        LOG.write_text(f"{lines[0]}\n\n{log_entry}\n{lines[1] if len(lines) > 1 else ''}", encoding="utf-8")
        created.append((str(LOG), "log"))

    table = Table(box=box.SIMPLE, show_header=True, padding=(0, 2))
    table.add_column("File written", style="cyan")
    table.add_column("Type", style="dim white")
    for path, kind in created:
        table.add_row(path, kind)

    console.print(Panel(
        table,
        title=f"[green]  ✅ Ingested: [white]{source_label}[/]  [/]",
        border_style="green",
    ))


def cmd_query(question: str | None = None):
    console.print(Rule("[bold cyan]  Query  [/]", style="cyan"))

    if question is None:
        question = Prompt.ask("[cyan]Your question[/]").strip()

    save = Confirm.ask("Save answer as a wiki page?", default=False)

    client = get_client()
    wiki_context = _gather_wiki_context(question, load_index())

    system = f"""You are an LLM Wiki Agent in query mode. Answer using only the pre-compiled wiki pages.
Always cite which wiki page each fact came from. Use rich markdown formatting.

<schema>
{load_schema()}
</schema>

<wiki_context>
{wiki_context}
</wiki_context>"""

    response = call_claude(client, system, f"Question: {question}", "Searching the wiki...")

    console.print(Panel(
        response,
        title=f"[bold cyan]  ❓ {question}  [/]",
        border_style="cyan",
        padding=(1, 2),
    ))

    if save:
        out = _save_query_as_page(question, response)
        console.print(f"[green]✅ Saved to[/] [cyan]{out}[/]")


def cmd_lint():
    console.print(Rule("[bold cyan]  Lint  [/]", style="cyan"))

    all_pages = []
    for md_file in WIKI_DIR.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        all_pages.append(f"=== {md_file} ===\n{content}")

    if not all_pages:
        console.print("[yellow]Wiki is empty.[/] Run [cyan]Init[/] then [cyan]Ingest[/] first.")
        return

    client = get_client()
    wiki_dump = "\n\n".join(all_pages)[:30000]

    system = f"""You are an LLM Wiki Agent in lint mode. Audit the wiki for:
1. Contradictions between pages
2. Orphaned pages (not in index.md)
3. Entity pages with missing sources
4. Stale or incomplete pages
5. Cross-reference gaps (mentioned but no page)

<schema>
{load_schema()}
</schema>"""

    response = call_claude(client, system, f"Audit this wiki:\n\n{wiki_dump}", "Auditing the wiki...")

    console.print(Panel(
        response,
        title="[bold yellow]  🔧 Lint Report  [/]",
        border_style="yellow",
        padding=(1, 2),
    ))


def cmd_status():
    console.print(Rule("[bold cyan]  Status  [/]", style="cyan"))

    if not INDEX.exists():
        console.print("[yellow]Wiki not initialized.[/] Run [cyan]Init[/] first.")
        return

    sources  = list((WIKI_DIR / "sources").glob("*.md"))  if (WIKI_DIR / "sources").exists()  else []
    entities = list((WIKI_DIR / "entities").glob("*.md")) if (WIKI_DIR / "entities").exists() else []

    last_ingest = "—"
    if LOG.exists():
        matches = re.findall(r"## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) — INGEST", LOG.read_text(encoding="utf-8"))
        if matches:
            last_ingest = matches[0]

    table = Table(box=box.SIMPLE, show_header=False, padding=(0, 3))
    table.add_column("label", style="dim white")
    table.add_column("value", style="bold bright_white")
    table.add_row("📄  Source pages", str(len(sources)))
    table.add_row("🏷️   Entity pages", str(len(entities)))
    table.add_row("🕐  Last ingest",  last_ingest)
    table.add_row("📁  Wiki dir",     str(WIKI_DIR.resolve()))

    console.print(Panel(
        Align.center(table),
        title="[bold cyan]  📊 Wiki Status  [/]",
        border_style="cyan",
    ))


# ── Interactive loop ──────────────────────────────────────────────────────────


COMMANDS = {
    "1": ("Init",   cmd_init),
    "2": ("Ingest", cmd_ingest),
    "3": ("Query",  cmd_query),
    "4": ("Lint",   cmd_lint),
    "5": ("Status", cmd_status),
}


def run():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    show_banner()

    while True:
        show_menu()
        choice = Prompt.ask("[bold cyan]Choose[/]", default="0").strip()

        if choice == "0":
            console.print()
            console.print(Panel(
                Align.center(Text("Goodbye. Your wiki will remember. 🧠", style="italic dim white")),
                border_style="dim cyan",
                box=box.ROUNDED,
                padding=(1, 4),
            ))
            console.print()
            break

        if choice not in COMMANDS:
            console.print("[red]Invalid choice.[/] Pick 1–5 or 0 to exit.\n")
            continue

        _, fn = COMMANDS[choice]
        console.print()
        try:
            fn()
        except KeyboardInterrupt:
            console.print("\n[dim]Cancelled.[/]")

        console.print()
        Prompt.ask("[dim]Press Enter to return to menu[/]", default="")
        show_banner()


if __name__ == "__main__":
    run()
