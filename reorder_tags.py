# -*- coding: utf-8 -*-
"""
Reorder first-line tags in .md files according to hierarchy from Иерархия_тегов.md.
Usage: python reorder_tags.py <folder>
Only processes files whose first line looks like a tag line (contains #tags).
"""

import re
import sys
from pathlib import Path

# Order from "Порядок сортировки тегов в файлах" (Иерархия_тегов.md)
TAG_ORDER = [
    "dc",
    "dc/dp",
    "dc/bnha",
    "dc/marvel",
    "dc/talon",
    "dc/dark_Bruce",
    "dc/ori",
    "dsmp",
    "dimentional_travel",
    "time_travel",
    "time_loop",
    "reincarnation",
    "reveal",
    "wings",
    "transformation",
    "de-aging",
    "dragon",
    "MahouShoujo",
    "magic",
    "ABO",
    "talon",
    "hurt-comfort",
    "trust_issues",
]

ORDER_INDEX = {tag: i for i, tag in enumerate(TAG_ORDER)}
UNIVERSE_END = ORDER_INDEX["dc/ori"] + 1
MAGIC_INDEX = ORDER_INDEX["MahouShoujo"]
UNKNOWN_INDEX = len(TAG_ORDER)


def tag_sort_key(tag: str) -> tuple:
    """Sort key: (group_index, sub_order)."""
    exact = ORDER_INDEX.get(tag)
    if exact is not None:
        return (exact, tag)
    if tag.startswith("dc/"):
        return (UNIVERSE_END, tag)
    if tag.startswith("MahouShoujo"):
        return (MAGIC_INDEX, tag)
    return (UNKNOWN_INDEX, tag)


def is_tag_line(line: str) -> bool:
    """True if line looks like a tag line (contains # and at least one #word)."""
    line = line.strip()
    if not line or "#" not in line:
        return False
    return bool(re.findall(r"#[\w/-]+", line))


def parse_tag_line(line: str) -> tuple[str | None, list[str]]:
    """
    Returns (prefix, list of tag names without #).
    prefix is e.g. 'Теги: ' or None if line starts with #.
    """
    stripped = line.strip()
    prefix = None
    if stripped.startswith("Теги:") or stripped.lower().startswith("tags:"):
        match = re.match(r"^(\s*Теги:\s*|\s*Tags:\s*)", stripped, re.I)
        if match:
            prefix = match.group(1)
            stripped = stripped[match.end() :]
    tags = re.findall(r"#([\w/-]+)", stripped)
    return (prefix, list(dict.fromkeys(tags)))  # unique, keep order for same-group


def build_tag_line(tags: list[str]) -> str:
    """Build first line: only #tag1 #tag2 ... (no 'Теги: ' prefix)."""
    return " ".join("#" + t for t in tags)


def reorder_tags_in_file(path: Path) -> bool:
    """Rewrite first line with tags in hierarchy order. Returns True if file was changed."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"[ERROR] {path}: {e}")
        return False

    lines = text.splitlines()
    if not lines:
        return False

    first = lines[0]
    if not is_tag_line(first):
        return False

    prefix, tags = parse_tag_line(first)
    if not tags:
        return False

    sorted_tags = sorted(tags, key=tag_sort_key)
    new_first = build_tag_line(sorted_tags)
    if new_first == first.strip():
        return False
    lines[0] = new_first
    path.write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return True


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python reorder_tags.py <folder>")
        sys.exit(1)

    folder = Path(sys.argv[1])
    if not folder.is_dir():
        print(f"Not a folder: {folder}")
        sys.exit(1)

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    changed = 0
    for md in folder.rglob("*.md"):
        if reorder_tags_in_file(md):
            changed += 1
            try:
                print(md.relative_to(folder).as_posix())
            except UnicodeEncodeError:
                print(md.name)

    print(f"Done. Changed {changed} file(s).")


if __name__ == "__main__":
    main()
