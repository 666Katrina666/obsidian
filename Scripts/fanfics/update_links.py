"""
Пересоздаёт ссылки на под-файлы в родительских файлах (Fanfics/).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

FANFICS_DIR = vault_root(__file__) / "Fanfics"

SUB_FILE_RE = re.compile(r"^(\d+)\.(\d+)[\. ]")


def scan_sub_files() -> dict[str, list[Path]]:
    groups: dict[str, list[tuple[int, Path]]] = {}
    for f in FANFICS_DIR.iterdir():
        if f.suffix != ".md":
            continue
        m = SUB_FILE_RE.match(f.name)
        if not m:
            continue
        parent_num = m.group(1)
        sub_num = int(m.group(2))
        groups.setdefault(parent_num, []).append((sub_num, f))

    return {
        num: [f for _, f in sorted(entries)]
        for num, entries in groups.items()
    }


def find_parent_file(parent_num: str) -> Path | None:
    prefix = f"{parent_num}. "
    for f in FANFICS_DIR.iterdir():
        if f.suffix == ".md" and f.name.startswith(prefix):
            return f
    return None


def rebuild_links(parent_path: Path, sub_files: list[Path]) -> bool:
    try:
        text = parent_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"! Cannot read {parent_path.name}: {e}")
        return False

    lines = text.splitlines()
    cleaned = [l for l in lines if not re.match(r"^\s*- \[\[.*\]\]\s*$", l)]

    while cleaned and not cleaned[-1].strip():
        cleaned.pop()

    new_links = [f"- [[{f.stem}]]" for f in sub_files]
    cleaned.extend(new_links)
    cleaned.append("")

    new_text = "\n".join(cleaned) + "\n"

    if new_text == text:
        return False

    try:
        parent_path.write_text(new_text, encoding="utf-8")
        return True
    except Exception as e:
        print(f"! Cannot write {parent_path.name}: {e}")
        return False


def main() -> None:
    if not FANFICS_DIR.exists():
        print(f"Directory not found: {FANFICS_DIR}")
        return

    sub_groups = scan_sub_files()
    if not sub_groups:
        print("No sub-files found in Fanfics directory.")
        return

    print(f"Found sub-file groups for {len(sub_groups)} parent numbers.\n")

    updated = 0
    unchanged = 0
    not_found = 0

    for parent_num in sorted(sub_groups, key=int):
        sub_files = sub_groups[parent_num]
        parent_file = find_parent_file(parent_num)

        if parent_file is None:
            print(f"! Parent #{parent_num} not found  (sub-files: {[f.name for f in sub_files]})")
            not_found += 1
            continue

        changed = rebuild_links(parent_file, sub_files)
        status = "Updated" if changed else "No changes"
        sub_names = ", ".join(f.name for f in sub_files)
        print(f"{status}: {parent_file.name}")
        print(f"         -> {sub_names}")
        if changed:
            updated += 1
        else:
            unchanged += 1

    print()
    print(f"Updated  : {updated}")
    print(f"Unchanged: {unchanged}")
    print(f"Not found: {not_found}")


if __name__ == "__main__":
    main()
