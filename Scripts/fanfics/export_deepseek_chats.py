# -*- coding: utf-8 -*-
"""Export Deepseek conversations.json to separate .md files.

Defaults: Beta/ and Fanfics/ under vault root (parent of Scripts/).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

VAULT = vault_root(__file__)

CONV_PATHS = [
    r"c:\Users\kiris\Downloads\deepseek_data-2026-02-14\conversations.json",
    r"c:\Users\kiris\Downloads\deepseek_data-2026-02-14 (1)\conversations.json",
    r"c:\Users\kiris\Downloads\deepseek_data-2026-02-14 (2)\conversations.json",
]

HEADER = """Теги: 

Описание: 

---
"""

SUB_FILE_RE = re.compile(r"^(\d+)\.(\d+)[\. ]")
PARENT_FILE_RE = re.compile(r"^(\d+)\.\s")


def max_parent_index(directory: str) -> int:
    if not os.path.isdir(directory):
        return 0
    n = 0
    for name in os.listdir(directory):
        if not name.endswith(".md"):
            continue
        if name.lower() == "rename_plan.md":
            continue
        m = SUB_FILE_RE.match(name)
        if m:
            n = max(n, int(m.group(1)))
            continue
        m = PARENT_FILE_RE.match(name)
        if m:
            n = max(n, int(m.group(1)))
    return n


def next_export_index(fanfics_dir: str, beta_dir: str) -> int:
    return max(max_parent_index(fanfics_dir), max_parent_index(beta_dir)) + 1


def safe_filename(title: str, index: int) -> str:
    if not title or not title.strip():
        title = "Conversation"
    clean = re.sub(r"[^\w\s\-]", " ", title, flags=re.UNICODE)
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = clean[:80] if len(clean) > 80 else clean
    return f"{index}. {clean}.md"


def walk_messages(mapping, node_id, acc):
    kids = (mapping.get(node_id) or {}).get("children") or []
    for k in kids:
        msg = (mapping.get(k) or {}).get("message")
        if msg:
            for frag in msg.get("fragments") or []:
                t = frag.get("type")
                c = frag.get("content")
                if c is not None and c.strip():
                    acc.append((t, c.strip()))
        walk_messages(mapping, k, acc)


def conversation_to_md(conv):
    mapping = conv.get("mapping") or {}
    parts = []
    walk_messages(mapping, "root", parts)
    lines = []
    for typ, content in parts:
        if typ == "REQUEST":
            lines.append("**Вы:**")
        else:
            lines.append("**Ассистент:**")
        lines.append("")
        lines.append(content)
        lines.append("")
    return "\n".join(lines).strip()


def run_export(
    json_paths: list[str],
    out_dir: str,
    fanfics_dir: str,
) -> int:
    all_convs = []
    for p in json_paths:
        if not os.path.isfile(p):
            print(f"Skip (not found): {p}")
            continue
        with open(p, "r", encoding="utf-8") as f:
            all_convs.extend(json.load(f))
        print(f"Loaded {p}")
    if not all_convs:
        print("No conversations to export.")
        return 0
    os.makedirs(out_dir, exist_ok=True)
    start = next_export_index(fanfics_dir, out_dir)
    written = 0
    for idx, conv in enumerate(all_convs):
        i = start + idx
        title = (conv.get("title") or "").strip() or f"Chat {i}"
        body = conversation_to_md(conv)
        name = safe_filename(title, i)
        path = os.path.join(out_dir, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(HEADER)
            f.write(body)
        print(path)
        written += 1
    print(f"Done: {written} files in {out_dir}")
    return written


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export DeepSeek conversations.json to .md")
    parser.add_argument(
        "--out",
        default=str(VAULT / "Beta"),
        help="Output directory (default: vault/Beta)",
    )
    parser.add_argument(
        "--fanfics",
        default=str(VAULT / "Fanfics"),
        help="Fanfics directory for next index",
    )
    parser.add_argument(
        "json_files",
        nargs="*",
        help="Path(s) to conversations.json (if empty, uses built-in CONV_PATHS)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    paths = [os.path.abspath(p) for p in args.json_files] if args.json_files else CONV_PATHS
    out_dir = os.path.abspath(args.out)
    fanfics_dir = os.path.abspath(args.fanfics)
    run_export(paths, out_dir, fanfics_dir)


if __name__ == "__main__":
    main()
