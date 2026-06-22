"""
Reads fanfic files numbered 366-717, extracts tags and first 400 chars
of the user's first prompt, writes to prompts_dump.txt in vault root.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

VAULT = vault_root(__file__)
FANFICS_DIR = VAULT / "Fanfics"
OUT_PATH = VAULT / "prompts_dump.txt"
PROMPT_CHARS = 400


def iter_files():
    entries = []
    for name in os.listdir(FANFICS_DIR):
        if not name.lower().endswith(".md"):
            continue
        m = re.match(r"^(\d+)", name)
        if not m:
            continue
        num = int(m.group(1))
        if num <= 365 or num > 717:
            continue
        entries.append((num, name))
    return sorted(entries, key=lambda x: (x[0], x[1]))


def extract_parts(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        return "", f"[read error: {e}]"

    lines = text.splitlines()
    tags = lines[0].strip() if lines else ""

    m = re.search(r"\*\*Вы:\*\*\s*\n(.*?)(?:\n\*\*Ассистент:\*\*|\Z)", text, re.DOTALL)
    prompt = m.group(1).strip() if m else text.strip()
    return tags, prompt[:PROMPT_CHARS]


def main():
    files = iter_files()
    print(f"Found {len(files)} files to dump.")

    with OUT_PATH.open("w", encoding="utf-8") as out:
        for idx, (num, filename) in enumerate(files, start=1):
            path = FANFICS_DIR / filename
            tags, prompt = extract_parts(path)
            out.write(f"=== {idx:03d}/{len(files)} ===\n")
            out.write(f"N: {num}\n")
            out.write(f"FILE: {filename}\n")
            out.write(f"TAGS: {tags}\n")
            out.write(f"PROMPT:\n{prompt}\n")
            out.write(f"=== END ===\n\n")

    print(f"Done. Written to {OUT_PATH}")


if __name__ == "__main__":
    main()
