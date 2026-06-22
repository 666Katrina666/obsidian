# -*- coding: utf-8 -*-
"""Теги фанфиков: прибавить (apply), пересчитать все (fix), один тег (single).

Без аргументов — интерактивное меню. Иначе подкоманды:
  python fanfic_tags.py apply [папка] [--dry-run]
  python fanfic_tags.py fix [--apply] [--limit N]
  python fanfic_tags.py single --tag ИМЯ [--apply] [--only-having|--only-missing] [--start-index I] [--end-index J]
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

OBSIDIAN_ROOT = vault_root(__file__)
CRITERIA_DIR = "tag_criteria"
FANFICS_DIR = "Fanfics"
ENCODING = "utf-8"
CONTENT_FILE = "1. Content.md"


def get_md_files(folder: str, exclude_content: bool) -> list[str]:
    paths = []
    for name in os.listdir(folder):
        if not name.endswith(".md"):
            continue
        if exclude_content and name == CONTENT_FILE:
            continue
        paths.append(os.path.join(folder, name))
    return sorted(paths)


def parse_tags_from_first_line(line: str) -> list[str]:
    if not line or not line.strip():
        return []
    line = line.strip()
    if line.lower().startswith("теги:"):
        line = line[5:].strip()
    tags = re.findall(r"#([^\s#]+)", line)
    return list(dict.fromkeys(tags))


def read_file(path: str) -> tuple[str, str]:
    with open(path, "r", encoding=ENCODING) as f:
        content = f.read()
    if "\n" in content:
        first, _rest = content.split("\n", 1)
        return first, content
    return content, content


def get_body_and_filename(content: str, path: str) -> str:
    if "\n" not in content:
        body = ""
    else:
        _first_line, rest = content.split("\n", 1)
        if "---" in rest:
            _, after = rest.split("---", 1)
            body = after
        else:
            body = rest
    filename = os.path.basename(path)
    return (body + "\n" + filename).strip()


def get_text_for_check(content: str, path: str) -> str:
    return get_body_and_filename(content, path)


def write_first_line(path: str, first_line: str, rest_content: str) -> None:
    with open(path, "w", encoding=ENCODING) as f:
        f.write(first_line + "\n" + rest_content)


def load_criteria_modules() -> list[tuple[str, object]]:
    criteria_path = OBSIDIAN_ROOT / CRITERIA_DIR
    if not criteria_path.is_dir():
        return []
    result: list[tuple[str, object]] = []
    for name in sorted(os.listdir(criteria_path)):
        if not name.endswith(".py") or name.startswith("_"):
            continue
        mod_path = criteria_path / name
        if not mod_path.is_file():
            continue
        spec = importlib.util.spec_from_file_location(
            "tag_criteria." + name[:-3], str(mod_path)
        )
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"Warning: skip {name}: {e}", file=sys.stderr)
            continue
        tag = getattr(mod, "TAG", None)
        check = getattr(mod, "check", None)
        if tag and callable(check):
            result.append((tag, check))
        else:
            print(f"Warning: {name} has no TAG or check()", file=sys.stderr)
    return result


def apply_dc_rule(tags: list[str]) -> list[str]:
    has_dc_slash = any(t.startswith("dc/") for t in tags)
    if has_dc_slash:
        tags = [t for t in tags if t != "dc"]
    return tags


def run_apply(folder: str, dry_run: bool) -> None:
    modules = load_criteria_modules()
    if not modules:
        print("No criteria modules found in", CRITERIA_DIR, file=sys.stderr)
        return
    md_files = get_md_files(folder, exclude_content=False)
    if not md_files:
        print("No .md files in", folder)
        return
    for path in md_files:
        first_line, content = read_file(path)
        existing = parse_tags_from_first_line(first_line)
        to_add = []
        for tag, check in modules:
            if tag in existing:
                continue
            try:
                if check(content):
                    to_add.append(tag)
            except Exception as e:
                print(
                    f"Warning: {os.path.basename(path)} tag {tag}: {e}",
                    file=sys.stderr,
                )
        merged = list(dict.fromkeys(existing + to_add))
        merged = apply_dc_rule(merged)
        new_first = "Теги: " + (" ".join("#" + t for t in merged) if merged else "")
        if new_first != first_line:
            if dry_run:
                print(path, "->", new_first)
            else:
                rest = content.split("\n", 1)[1] if "\n" in content else ""
                write_first_line(path, new_first, rest)
                print(path)


def run_fix(dry_run: bool, limit: int | None) -> None:
    fanfics_path = str(OBSIDIAN_ROOT / FANFICS_DIR)
    if not os.path.isdir(fanfics_path):
        print("Not a directory:", fanfics_path, file=sys.stderr)
        return

    modules = load_criteria_modules()
    if not modules:
        print("No criteria modules found in", CRITERIA_DIR, file=sys.stderr)
        return

    md_files = get_md_files(fanfics_path, exclude_content=True)
    if limit is not None:
        md_files = md_files[:limit]
    if not md_files:
        print("No .md files in", fanfics_path)
        return

    count_before: dict[str, int] = {}
    count_after: dict[str, int] = {}

    for path in md_files:
        first_line, content = read_file(path)
        existing = parse_tags_from_first_line(first_line)
        for t in existing:
            count_before[t] = count_before.get(t, 0) + 1

        text = get_body_and_filename(content, path)
        new_tags = []
        for tag, check in modules:
            try:
                if check(text):
                    new_tags.append(tag)
            except Exception as e:
                print(
                    f"Warning: {os.path.basename(path)} tag {tag}: {e}",
                    file=sys.stderr,
                )
        new_tags = apply_dc_rule(list(dict.fromkeys(new_tags)))
        for t in new_tags:
            count_after[t] = count_after.get(t, 0) + 1

        new_first = "Теги: " + (
            " ".join("#" + t for t in sorted(new_tags)) if new_tags else ""
        )
        if new_first != first_line:
            if not dry_run:
                rest = content.split("\n", 1)[1] if "\n" in content else ""
                write_first_line(path, new_first, rest)

    all_tags = sorted(set(count_before) | set(count_after))
    print("\nТег                    | До (файлов) | После (файлов)")
    print("-" * 52)
    for tag in all_tags:
        b = count_before.get(tag, 0)
        a = count_after.get(tag, 0)
        print(f"#{tag:<22} | {b:>11} | {a:>14}")
    print("-" * 52)
    print(
        f"Обработано файлов: {len(md_files)}. Режим: "
        f"{'dry-run (без записи)' if dry_run else '--apply (изменения записаны)'}"
    )


def load_single_criteria(tag_name: str):
    criteria_path = OBSIDIAN_ROOT / CRITERIA_DIR
    if not criteria_path.is_dir():
        raise SystemExit(f"No criteria directory: {criteria_path}")
    found_check = None
    found_file = None
    for name in sorted(os.listdir(criteria_path)):
        if not name.endswith(".py") or name.startswith("_"):
            continue
        mod_path = criteria_path / name
        spec = importlib.util.spec_from_file_location(
            "tag_criteria." + name[:-3], str(mod_path)
        )
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"Warning: skip {name}: {e}", file=sys.stderr)
            continue
        tag = getattr(mod, "TAG", None)
        check = getattr(mod, "check", None)
        if tag == tag_name and callable(check):
            found_check = check
            found_file = name
            break
    if not found_check:
        raise SystemExit(f"Tag '{tag_name}' not found in {CRITERIA_DIR}/")
    print(f"Using criteria from {CRITERIA_DIR}/{found_file} for tag '{tag_name}'")
    return found_check


def run_single(
    tag_name: str,
    only_having: bool,
    only_missing: bool,
    start_index: int | None,
    end_index: int | None,
    dry_run: bool,
) -> None:
    fanfics_path = str(OBSIDIAN_ROOT / FANFICS_DIR)
    if not os.path.isdir(fanfics_path):
        raise SystemExit(f"Not a directory: {fanfics_path}")

    check = load_single_criteria(tag_name)
    md_files = get_md_files(fanfics_path, exclude_content=True)
    if not md_files:
        print("No .md files in", fanfics_path)
        return

    total = len(md_files)
    added = removed = skipped = unchanged = 0
    had_before = has_after = 0

    if start_index is not None or end_index is not None:
        si = start_index or 1
        ei = end_index or total
        md_files = md_files[si - 1 : ei]
        print(f"Index range: {si}..{ei} (files: {len(md_files)})")

    for path in md_files:
        first_line, content = read_file(path)
        tags = parse_tags_from_first_line(first_line)
        has_tag = tag_name in tags
        if has_tag:
            had_before += 1

        if only_having and not has_tag:
            skipped += 1
            continue
        if only_missing and has_tag:
            skipped += 1
            continue

        text = get_text_for_check(content, path)
        try:
            should_have = bool(check(text))
        except Exception as e:
            print(
                f"Warning: {os.path.basename(path)} check failed: {e}",
                file=sys.stderr,
            )
            skipped += 1
            continue

        new_tags = list(tags)
        changed = False

        if should_have and not has_tag:
            new_tags.append(tag_name)
            changed = True
            added += 1
        elif not should_have and has_tag:
            new_tags = [t for t in new_tags if t != tag_name]
            changed = True
            removed += 1

        new_tags = apply_dc_rule(new_tags)
        if tag_name in new_tags:
            has_after += 1

        new_first = "Теги: " + (" ".join("#" + t for t in new_tags) if new_tags else "")
        if changed:
            rel = os.path.relpath(path, str(OBSIDIAN_ROOT))
            if dry_run:
                print(f"[DRY] {rel} -> {new_first}")
            else:
                rest = content.split("\n", 1)[1] if "\n" in content else ""
                write_first_line(path, new_first, rest)
                print(rel)
        else:
            unchanged += 1

    print("\n=== Single-tag summary ===")
    print(f"Tag: #{tag_name}")
    print(f"Files scanned: {len(md_files)} (of total {total})")
    print(f"Had tag before: {had_before}")
    print(f"Have tag after: {has_after}")
    print(
        f"Added: {added}, removed: {removed}, unchanged: {unchanged}, "
        f"skipped (filtered): {skipped}"
    )
    print("Mode:", "dry-run" if dry_run else "APPLY (written)")


def _prompt(msg: str, default: str = "") -> str:
    tail = f" [{default}]" if default else ""
    s = input(f"{msg}{tail}: ").strip()
    return s if s else default


def interactive_menu() -> None:
    print(
        "\n=== Теги фанфиков (tag_criteria) ===\n"
        "1. Прибавить недостающие теги (apply) — не снимает уже стоящие\n"
        "2. Пересчитать все теги по тексту (fix) — только Fanfics/\n"
        "3. Один тег: добавить/снять по критерию (single)\n"
        "0. Выход\n"
    )
    choice = _prompt("Выбор", "0")
    if choice == "1":
        default_folder = str(OBSIDIAN_ROOT / FANFICS_DIR)
        folder = _prompt("Папка с .md", default_folder) or default_folder
        dry = _prompt("Только просмотр без записи? (y/n)", "y").lower() != "n"
        run_apply(folder, dry_run=dry)
    elif choice == "2":
        apply_changes = _prompt("Записать изменения на диск? (y/n)", "n").lower() == "y"
        lim_s = _prompt("Лимит файлов (пусто = все)", "")
        limit = int(lim_s) if lim_s.isdigit() else None
        run_fix(dry_run=not apply_changes, limit=limit)
    elif choice == "3":
        tag = _prompt("Имя тега без # (например ABO или dc/talon)", "")
        if not tag:
            print("Отмена.")
            return
        apply_changes = _prompt("Записать изменения? (y/n)", "n").lower() == "y"
        oh = _prompt("Только файлы где тег уже есть? (y/n)", "n").lower() == "y"
        om = _prompt("Только файлы где тега нет? (y/n)", "n").lower() == "y"
        if oh and om:
            print("Нельзя оба фильтра.")
            return
        run_single(
            tag_name=tag,
            only_having=oh,
            only_missing=om,
            start_index=None,
            end_index=None,
            dry_run=not apply_changes,
        )
    elif choice == "0":
        print("Выход.")
    else:
        print("Неизвестный пункт.")


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fanfic tags: apply / fix / single")
    sub = p.add_subparsers(dest="cmd", required=True)

    pa = sub.add_parser("apply", help="Add missing tags only (full file text for checks)")
    pa.add_argument(
        "folder",
        nargs="?",
        default=None,
        help="Folder with .md (default: Fanfics in vault)",
    )
    pa.add_argument("--dry-run", action="store_true", help="Do not write files")

    pf = sub.add_parser("fix", help="Recompute all tags from Fanfics/ body + filename")
    pf.add_argument("--apply", action="store_true", help="Write changes (default dry-run)")
    pf.add_argument("--limit", type=int, default=None, help="Process only first N files")

    ps = sub.add_parser("single", help="Recompute one tag in Fanfics/")
    ps.add_argument("--tag", required=True, help="Tag without #")
    ps.add_argument("--only-having", action="store_true")
    ps.add_argument("--only-missing", action="store_true")
    ps.add_argument("--start-index", type=int, default=None)
    ps.add_argument("--end-index", type=int, default=None)
    ps.add_argument("--apply", action="store_true")

    return p


def main_cli(argv: list[str] | None) -> None:
    parser = build_arg_parser()
    args = parser.parse_args(argv)

    if args.cmd == "apply":
        folder = args.folder or str(OBSIDIAN_ROOT / FANFICS_DIR)
        if not os.path.isdir(folder):
            print("Not a directory:", folder, file=sys.stderr)
            sys.exit(1)
        run_apply(folder, dry_run=args.dry_run)

    elif args.cmd == "fix":
        run_fix(dry_run=not args.apply, limit=args.limit)

    elif args.cmd == "single":
        if args.only_having and args.only_missing:
            parser.error("Use at most one of --only-having / --only-missing")
        run_single(
            tag_name=args.tag,
            only_having=args.only_having,
            only_missing=args.only_missing,
            start_index=args.start_index,
            end_index=args.end_index,
            dry_run=not args.apply,
        )


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        interactive_menu()
    elif argv[0] in ("-h", "--help"):
        build_arg_parser().print_help()
    else:
        main_cli(argv)


if __name__ == "__main__":
    main()
