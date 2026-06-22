"""
Renumber Fanfics:

- Находит пробелы в нумерации (gaps) и группы с "лишними" номерами в хвосте (overflow).
- Переименовывает только overflow‑группы (родитель + подфайлы) так, чтобы они заняли gaps.
- Нормализует подномера внутри групп с разрывами (например, 466.2 → 466.1).
- Обновляет блоки wikilinks в родителях по аналогии с update_links.py.

Поддерживает режим --dry-run, в котором только печатает план действий.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

FANFICS_DIR = vault_root(__file__) / "Fanfics"

PARENT_RE = re.compile(r"^(\d+)[\. ]")
SUB_FILE_RE = re.compile(r"^(\d+)\.(\d+)[\. ]")


@dataclass
class Group:
    parent_num: int
    parent: Optional[Path] = None
    subs: Dict[int, Path] = field(default_factory=dict)


def debug(msg: str) -> None:
    print(msg)


def scan_groups() -> Dict[int, Group]:
    groups: Dict[int, Group] = {}

    if not FANFICS_DIR.exists():
        raise SystemExit(f"Directory not found: {FANFICS_DIR}")

    for f in FANFICS_DIR.iterdir():
        if f.suffix != ".md":
            continue
        if f.name.lower() == "rename_plan.md":
            continue

        name = f.name

        m_sub = SUB_FILE_RE.match(name)
        if m_sub:
            parent_num = int(m_sub.group(1))
            sub_num = int(m_sub.group(2))
            g = groups.setdefault(parent_num, Group(parent_num=parent_num))
            g.subs[sub_num] = f
            continue

        m_parent = PARENT_RE.match(name)
        if not m_parent:
            continue
        parent_num = int(m_parent.group(1))
        g = groups.setdefault(parent_num, Group(parent_num=parent_num))
        g.parent = f

    return groups


def build_renumber_plan(groups: Dict[int, Group]) -> Tuple[Dict[int, int], Dict[Tuple[int, int], int]]:
    if not groups:
        return {}, {}

    parent_nums = sorted(groups.keys())
    max_parent = max(parent_nums)
    max_valid = len(parent_nums)
    existing = set(parent_nums)
    gaps: List[int] = [n for n in range(1, max_valid + 1) if n not in existing]
    gaps.sort()
    overflow_nums: List[int] = [n for n in parent_nums if n > max_valid]
    overflow_nums.sort(reverse=True)

    parent_map: Dict[int, int] = {}
    for old_parent, gap in zip(overflow_nums, gaps):
        parent_map[old_parent] = gap
    for n in parent_nums:
        parent_map.setdefault(n, n)

    sub_map: Dict[Tuple[int, int], int] = {}
    for parent_num, g in groups.items():
        if not g.subs:
            continue
        old_sub_nums = sorted(g.subs.keys())
        desired = list(range(1, len(old_sub_nums) + 1))
        if old_sub_nums == desired:
            continue
        for old, new in zip(old_sub_nums, desired):
            sub_map[(parent_num, old)] = new

    return parent_map, sub_map


def make_parent_new_name(old_name: str, old_parent: int, new_parent: int) -> str:
    if old_parent == new_parent:
        return old_name
    prefix = str(old_parent)
    assert old_name.startswith(prefix)
    return f"{new_parent}{old_name[len(prefix):]}"


def make_sub_new_name(
    old_name: str, old_parent: int, new_parent: int, old_sub: int, new_sub: int
) -> str:
    if old_parent == new_parent and old_sub == new_sub:
        return old_name
    m = SUB_FILE_RE.match(old_name)
    if not m:
        rest = ""
        dot_idx = old_name.find(".")
        if dot_idx != -1:
            rest = old_name[dot_idx + 1 :]
        return f"{new_parent}.{new_sub}.{rest}" if rest else f"{new_parent}.{new_sub}.md"
    suffix = old_name[m.end(2) :]
    return f"{new_parent}.{new_sub}{suffix}"


def compute_file_moves(
    groups: Dict[int, Group],
    parent_map: Dict[int, int],
    sub_map: Dict[Tuple[int, int], int],
) -> Tuple[Dict[Path, Path], List[int]]:
    moves: Dict[Path, Path] = {}
    affected_parents: set[int] = set()

    for parent_num, g in groups.items():
        new_parent_num = parent_map.get(parent_num, parent_num)

        if g.parent is not None:
            new_name = make_parent_new_name(g.parent.name, parent_num, new_parent_num)
            if new_name != g.parent.name:
                moves[g.parent] = g.parent.with_name(new_name)
                affected_parents.add(new_parent_num)

        for old_sub, path in g.subs.items():
            new_sub = sub_map.get((parent_num, old_sub), old_sub)
            if new_sub != old_sub or new_parent_num != parent_num:
                new_name = make_sub_new_name(
                    path.name, parent_num, new_parent_num, old_sub, new_sub
                )
                moves[path] = path.with_name(new_name)
                affected_parents.add(new_parent_num)

    return moves, sorted(affected_parents)


def apply_moves(moves: Dict[Path, Path], dry_run: bool) -> None:
    if not moves:
        debug("No files to rename.")
        return

    debug(f"Files to rename: {len(moves)}")

    if dry_run:
        for old, new in sorted(moves.items(), key=lambda kv: str(kv[0])):
            if old == new:
                continue
            debug(f"[DRY-RUN] {old.name}  ->  {new.name}")
        return

    temp_map: Dict[Path, Path] = {}
    for old, new in moves.items():
        if old == new:
            continue
        temp = old.with_name(f"TMP_RENUMBER_{old.name}")
        debug(f"TMP: {old.name}  ->  {temp.name}")
        old.rename(temp)
        temp_map[temp] = new

    for temp, final in temp_map.items():
        debug(f"REN: {temp.name}  ->  {final.name}")
        temp.rename(final)


def update_wikilinks(affected_parents: List[int], dry_run: bool) -> None:
    if not affected_parents:
        debug("No parents affected, skip wikilinks rebuild.")
        return

    try:
        from update_links import scan_sub_files, find_parent_file, rebuild_links
    except Exception as e:
        debug(f"Cannot import update_links: {e}")
        return

    sub_groups = scan_sub_files()
    if not sub_groups:
        debug("No sub-files found, skip wikilinks rebuild.")
        return

    for parent_num in sorted(set(affected_parents)):
        parent_str = str(parent_num)
        sub_files = sub_groups.get(parent_str)
        if not sub_files:
            continue
        parent_file = find_parent_file(parent_str)
        if parent_file is None:
            continue

        if dry_run:
            names = ", ".join(f.name for f in sub_files)
            debug(
                f"[DRY-RUN] Would rebuild links in {parent_file.name} for sub-files: {names}"
            )
            continue

        changed = rebuild_links(parent_file, sub_files)
        status = "Updated" if changed else "No changes"
        debug(f"{status} wikilinks in {parent_file.name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Renumber Fanfics files.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Только показать план действий, без изменения файлов.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dry_run = args.dry_run

    debug(f"Fanfics directory: {FANFICS_DIR}")
    debug(f"Dry-run mode: {dry_run}")
    debug("")

    groups = scan_groups()
    if not groups:
        debug("No numbered groups found in Fanfics directory.")
        return

    debug(f"Found {len(groups)} parent groups.")

    parent_map, sub_map = build_renumber_plan(groups)

    debug("")
    debug("Parent mapping (old -> new) for groups that change:")
    for old_parent, new_parent in sorted(parent_map.items()):
        if old_parent != new_parent:
            debug(f"  {old_parent} -> {new_parent}")

    moves, affected_parents = compute_file_moves(groups, parent_map, sub_map)
    debug("")
    apply_moves(moves, dry_run=dry_run)

    debug("")
    update_wikilinks(affected_parents, dry_run=dry_run)


if __name__ == "__main__":
    main()
