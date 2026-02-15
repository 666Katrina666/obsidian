# -*- coding: utf-8 -*-
"""Export Deepseek conversations.json to separate .md files.
Each file: Теги:\n\nОписание:\n\n---\n + chat content.
"""
import json
import os
import re
import sys

CONV_PATHS = [
    r"c:\Users\kiris\Downloads\deepseek_data-2026-02-14\conversations.json",
    r"c:\Users\kiris\Downloads\deepseek_data-2026-02-14 (1)\conversations.json",
    r"c:\Users\kiris\Downloads\deepseek_data-2026-02-14 (2)\conversations.json",
]
OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))


def max_existing_index():
    """Largest number in existing NN. title.md / NNN. title.md."""
    n = 0
    for name in os.listdir(OUT_DIR):
        if name.endswith(".md"):
            m = re.match(r"^(\d+)\.\s", name)
            if m:
                n = max(n, int(m.group(1)))
    return n

HEADER = """Теги: 

Описание: 

---
"""


def safe_filename(title, index):
    """Short safe filename: number and first words of title."""
    if not title or not title.strip():
        title = "Conversation"
    # leave letters, digits, spaces, hyphen; collapse spaces
    clean = re.sub(r"[^\w\s\-]", " ", title, flags=re.UNICODE)
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = clean[:60] if len(clean) > 60 else clean
    return f"{index:03d}. {clean}.md"


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


def main():
    paths_to_load = sys.argv[1:] if len(sys.argv) > 1 else CONV_PATHS
    all_convs = []
    for p in paths_to_load:
        if not os.path.isfile(p):
            print(f"Skip (not found): {p}")
            continue
        with open(p, "r", encoding="utf-8") as f:
            all_convs.extend(json.load(f))
        print(f"Loaded {p}")
    if not all_convs:
        print("No conversations to export.")
        return
    if not os.path.isdir(OUT_DIR):
        os.makedirs(OUT_DIR)
    start = max_existing_index() + 1 if os.path.isdir(OUT_DIR) else 1
    for idx, conv in enumerate(all_convs):
        i = start + idx
        title = (conv.get("title") or "").strip() or f"Chat {i}"
        body = conversation_to_md(conv)
        name = safe_filename(title, i)
        path = os.path.join(OUT_DIR, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(HEADER)
            f.write(body)
        print(path)
    print(f"Done: {len(all_convs)} files in {OUT_DIR}")


if __name__ == "__main__":
    main()
