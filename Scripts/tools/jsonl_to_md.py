"""
Converts a Claude Code session transcript (.jsonl) into a readable Markdown
chat log using the vault convention (**Вы:** / **Ассистент:**).

Keeps only user and assistant text: tool calls, tool results, system reminders
and slash-command wrappers are dropped. The result keeps the source file name
with a .md suffix.

Usage:
    python jsonl_to_md.py <out_dir> <source.jsonl>
    python jsonl_to_md.py <out_dir> <sessions_dir>     # takes the newest .jsonl
    python jsonl_to_md.py <out_dir> <source.jsonl> --tags "#claude #dsmp"
    python jsonl_to_md.py <out_dir> <source.jsonl> --name dsmp-cycles
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SYSTEM_REMINDER_RE = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
COMMAND_TAG_RE = re.compile(
    r"<(?:local-)?command-[a-z-]+>.*?</(?:local-)?command-[a-z-]+>", re.DOTALL
)

USER_LABEL = "Вы"
ASSISTANT_LABEL = "Ассистент"


def resolve_source(raw: str) -> Path:
    """Accepts a .jsonl file or a directory; for a directory takes the newest."""
    path = Path(raw).expanduser()
    if path.is_dir():
        candidates = sorted(
            path.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        if not candidates:
            sys.exit(f"No .jsonl files in {path}")
        return candidates[0]
    if not path.is_file():
        sys.exit(f"Source not found: {path}")
    return path


def collect_text(content) -> str:
    """Pulls plain text out of a message body, stripping service markup."""
    if content is None:
        return ""

    if isinstance(content, str):
        parts = [content]
    else:
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]

    text = "\n\n".join(part for part in parts if part)
    text = SYSTEM_REMINDER_RE.sub("", text)
    text = COMMAND_TAG_RE.sub("", text)
    return text.strip()


def iter_messages(source: Path):
    """Yields (role, text) for every user/assistant entry that carries text."""
    with source.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            role = entry.get("type")
            if role not in ("user", "assistant") or entry.get("isMeta"):
                continue

            message = entry.get("message")
            if not isinstance(message, dict):
                continue

            text = collect_text(message.get("content"))
            if text:
                yield role, text


def build_markdown(source: Path, tags: str, user_label: str, assistant_label: str) -> tuple[str, int]:
    chunks: list[str] = []
    if tags:
        chunks.append(tags.strip())

    last_role = ""
    turns = 0

    for role, text in iter_messages(source):
        # consecutive entries of the same speaker merge under one label
        if role != last_role:
            label = user_label if role == "user" else assistant_label
            chunks.append(f"**{label}:**")
            last_role = role
            turns += 1
        chunks.append(text)

    return "\n\n".join(chunks) + "\n", turns


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert a Claude Code .jsonl session into a Markdown chat log."
    )
    parser.add_argument("out_dir", help="Folder to write the .md into")
    parser.add_argument("source", help="Path to a .jsonl file, or a folder of sessions")
    parser.add_argument("--tags", default="", help="First line of the file, e.g. \"#claude #dsmp\"")
    parser.add_argument("--name", default="", help="Output file name without extension")
    parser.add_argument("--user-label", default=USER_LABEL)
    parser.add_argument("--assistant-label", default=ASSISTANT_LABEL)
    args = parser.parse_args()

    source = resolve_source(args.source)
    out_dir = Path(args.out_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)

    stem = args.name.strip() or source.stem
    out_path = out_dir / f"{stem}.md"

    markdown, turns = build_markdown(
        source, args.tags, args.user_label, args.assistant_label
    )
    if turns == 0:
        sys.exit(f"No dialogue found in {source}")

    out_path.write_text(markdown, encoding="utf-8", newline="\n")

    size_kb = out_path.stat().st_size / 1024
    print(f"Source: {source}")
    print(f"Done: {out_path} ({turns} turns, {size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
