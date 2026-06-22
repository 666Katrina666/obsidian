# -*- coding: utf-8 -*-
"""Generic fix for a dc/* sub-tag: sync tag with criteria; on remove, add #dc if needed.

Usage:
  python Scripts/tags/fix_dc_subtag.py <tag_module>          # dry run
  python Scripts/tags/fix_dc_subtag.py <tag_module> --apply  # apply

Example:
  python Scripts/tags/fix_dc_subtag.py dc_talon
  python Scripts/tags/fix_dc_subtag.py dc_dp --apply
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

OBSIDIAN_ROOT = vault_root(__file__)
FANFICS = OBSIDIAN_ROOT / "Fanfics"
EXCLUDE = {"1. Content.md"}


def parse_tags(first_line: str) -> list[str]:
    m = re.match(r"Теги:\s*(.*)", first_line, re.IGNORECASE)
    if not m:
        return []
    return re.findall(r"#[\w/.-]+", m.group(1))


def build_tag_line(tags: list[str]) -> str:
    return "Теги: " + " ".join(tags)


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag_module", help="Module name without .py (e.g. dc_talon, dc_dp)")
    parser.add_argument("--apply", action="store_true", help="Write files")
    args = parser.parse_args()

    module_path = OBSIDIAN_ROOT / "tag_criteria" / f"{args.tag_module}.py"
    if not module_path.is_file():
        print(f"Module not found: {module_path}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location(args.tag_module, str(module_path))
    if spec is None or spec.loader is None:
        sys.exit(1)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    TAG = mod.TAG
    HASHTAG = f"#{TAG}"
    print(f"Processing tag: {HASHTAG}")

    dry_run = not args.apply
    removed = added = unchanged = 0
    changes_log: list[str] = []

    files = sorted(
        f
        for f in FANFICS.iterdir()
        if f.suffix == ".md" and f.name not in EXCLUDE
    )
    for path in files:
        content = path.read_text(encoding="utf-8")
        lines = content.split("\n")
        first = lines[0]
        body = "\n".join(lines[1:]) if len(lines) > 1 else ""

        old_tags = parse_tags(first)
        had_tag = HASHTAG in old_tags
        now_matches = mod.check(body)

        if had_tag == now_matches:
            unchanged += 1
            continue

        new_tags = list(old_tags)

        if had_tag and not now_matches:
            new_tags = [t for t in new_tags if t != HASHTAG]
            has_other_dc_slash = any(t.startswith("#dc/") for t in new_tags)
            if not has_other_dc_slash and "#dc" not in new_tags:
                new_tags.insert(0, "#dc")
            removed += 1
            changes_log.append(f"  REMOVE {TAG} → +#dc  | {path.name}")

        elif not had_tag and now_matches:
            new_tags = [t for t in new_tags if t != "#dc"]
            if HASHTAG not in new_tags:
                new_tags.insert(0, HASHTAG)
            added += 1
            changes_log.append(f"  ADD {TAG}  | {path.name}")

        if not dry_run:
            new_first = build_tag_line(new_tags)
            path.write_text(new_first + "\n" + body, encoding="utf-8")

    mode = "[DRY RUN]" if dry_run else "[APPLIED]"
    print(f"{mode}")
    print(f"  {TAG} removed (→ #dc added): {removed}")
    print(f"  {TAG} added   (← #dc removed): {added}")
    print(f"  unchanged: {unchanged}")
    if changes_log:
        print()
        print("Changes:")
        for line in changes_log:
            print(line)


if __name__ == "__main__":
    main()
