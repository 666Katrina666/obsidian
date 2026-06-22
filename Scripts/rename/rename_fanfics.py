# -*- coding: utf-8 -*-
"""Переименование фанфиков: план через Claude, применение плана, RU→EN по имени файла.

Без аргументов — меню. Подкоманды: suggest | apply | ru2en
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

OBSIDIAN_ROOT = vault_root(__file__)
FANFICS_DIR = OBSIDIAN_ROOT / "Fanfics"
PLAN_PATH = OBSIDIAN_ROOT / "rename_plan.md"

FANFIC_TAG_HINTS = (
    "#dc",
    "#dp",
    "#dc/dp",
    "#batfamily",
    "#batfam",
)
MAX_FILENAME_LEN = 105


def iter_fanfic_files():
    if not FANFICS_DIR.exists():
        raise SystemExit(f"Directory not found: {FANFICS_DIR}")
    for name in os.listdir(FANFICS_DIR):
        if not name.lower().endswith(".md"):
            continue
        m = re.match(r"^(\d+)", name)
        if not m:
            continue
        num = int(m.group(1))
        if num <= 365 or num > 717:
            continue
        yield num, name


def load_already_processed() -> set[str]:
    processed: set[str] = set()
    if not PLAN_PATH.exists():
        return processed
    with PLAN_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) != 3:
                continue
            _status, old_name, _new_name = parts
            if old_name in ("Старое имя", "Old name"):
                continue
            if old_name:
                processed.add(old_name)
    return processed


def ensure_plan_header() -> None:
    if PLAN_PATH.exists():
        return
    with PLAN_PATH.open("w", encoding="utf-8") as f:
        f.write("| Статус | Старое имя | Новое имя |\n")
        f.write("|--------|-----------|----------|\n")


def extract_prompt_parts(path: Path) -> tuple[str, str]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    tags_line = lines[0].strip() if lines else ""
    m = re.search(r"\*\*Вы:\*\*\s*\n(.*?)(?:\n\*\*Ассистент:\*\*|\Z)", text, re.DOTALL)
    if m:
        prompt_text = m.group(1).strip()
    else:
        prompt_text = text.strip()
    prompt_snippet = prompt_text[:1000]
    return tags_line, prompt_snippet


def is_fanfic_by_tags(tags_line: str) -> bool:
    tags_lower = tags_line.lower()
    return any(hint in tags_lower for hint in FANFIC_TAG_HINTS)


def postprocess_new_name(raw: str, number: int) -> str:
    line = ""
    for l in raw.splitlines():
        l = l.strip()
        if l:
            line = l
            break
    if not line:
        line = f"{number}. Untitled.md"
    line = line.strip("`\"' ")
    if not line.lower().endswith(".md"):
        line = f"{line}.md"
    m = re.match(r"^(\d+)", line)
    if not m or int(m.group(1)) != number:
        base = re.sub(r"^\d+(\.\d+)?\s*[.-]\s*", "", line)
        line = f"{number}. {base}".strip()
    if len(line) > MAX_FILENAME_LEN:
        base, ext = os.path.splitext(line)
        allowed = MAX_FILENAME_LEN - len(ext)
        if allowed <= 0:
            return f"{number}.md"[:MAX_FILENAME_LEN]
        base = base[:allowed]
        line = base + ext
    return line


def build_prompt(number: int, tags: str, snippet: str) -> str:
    return (
        "You help to rename Obsidian markdown files with chats and fanfic prompts.\n"
        "Given the file number, tags, and the first 1000 characters of the user's prompt, "
        "propose a NEW filename.\n\n"
        "Requirements:\n"
        f'- Format: "{number}. Title - Short description.md" (or keep existing sub-numbering if present in the text).\n'
        "- Language: English, in the same style as existing files (short, fandom-style titles).\n"
        f"- Maximum length: {MAX_FILENAME_LEN} characters INCLUDING the `.md` extension.\n"
        "- The title should reflect the main idea of the prompt (character, transformation, situation).\n"
        "- Do NOT include slashes, quotes or other characters illegal in Windows filenames.\n"
        "- Answer with ONE line: only the final filename, no explanations, no markdown.\n\n"
        f"File number: {number}\n"
        f"Tags: {tags}\n"
        "User prompt (first 1000 characters):\n"
        "-----\n"
        f"{snippet}\n"
        "-----\n"
    )


def cmd_suggest() -> None:
    from anthropic import Anthropic

    client = Anthropic()
    files = sorted(iter_fanfic_files(), key=lambda x: (x[0], x[1]))
    if not files:
        print("No matching files (numbers > 365 and <= 717) found in Fanfics.")
        return
    already = load_already_processed()
    ensure_plan_header()
    print(f"Total candidate files: {len(files)}")
    print(f"Already in rename_plan.md: {len(already)}")
    for idx, (num, filename) in enumerate(files, start=1):
        if filename in already:
            print(f"[{idx}/{len(files)}] Skipping already processed: {filename}")
            continue
        path = FANFICS_DIR / filename
        print(f"[{idx}/{len(files)}] Processing: {filename}")
        try:
            tags, snippet = extract_prompt_parts(path)
        except Exception as e:
            print(f"  ! Error reading file: {e}")
            status = "❌"
            new_name = filename
        else:
            status = "✅" if is_fanfic_by_tags(tags) else "⚠️"
            prompt = build_prompt(num, tags, snippet)
            try:
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=128,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}],
                )
                text_blocks = []
                for block in response.content:
                    if getattr(block, "type", None) == "text":
                        text_blocks.append(block.text)
                raw = "".join(text_blocks) if text_blocks else str(response)
                new_name = postprocess_new_name(raw, num)
                print(f"  → Suggested: {new_name}")
            except Exception as e:
                print(f"  ! API error: {e}")
                status = "❌"
                new_name = filename
        with PLAN_PATH.open("a", encoding="utf-8") as plan:
            plan.write(f"| {status} | {filename} | {new_name} |\n")
        time.sleep(0.3)
    print("Done. Review rename_plan.md before apply.")


def parse_plan_rows() -> list[tuple[str, str, str]]:
    rows = []
    if not PLAN_PATH.exists():
        print(f"Plan file not found: {PLAN_PATH}")
        return rows
    with PLAN_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.startswith("|"):
                continue
            parts = [p.strip() for p in line.split("|")[1:-1]]
            if len(parts) != 3:
                continue
            status, old_name, new_name = parts
            if old_name in ("Старое имя", "Old name") or status.startswith("-"):
                continue
            rows.append((status, old_name, new_name))
    return rows


def cmd_apply() -> None:
    if not FANFICS_DIR.exists():
        print(f"Directory not found: {FANFICS_DIR}")
        return
    rows = parse_plan_rows()
    if not rows:
        print("No rows found in rename_plan.md.")
        return
    applied = skipped = errors = 0
    for status, old_name, new_name in rows:
        if status != "✅":
            skipped += 1
            continue
        if not old_name or not new_name or old_name == new_name:
            skipped += 1
            continue
        src = FANFICS_DIR / old_name
        dst = FANFICS_DIR / new_name
        if not src.exists():
            print(f"! Source not found, skipping: {src}")
            errors += 1
            continue
        if dst.exists():
            print(f"! Destination already exists, skipping: {dst}")
            errors += 1
            continue
        try:
            os.rename(src, dst)
            applied += 1
            print(f"Renamed: {old_name}  ->  {new_name}")
        except Exception as e:
            print(f"! Error renaming {old_name} -> {new_name}: {e}")
            errors += 1
    print()
    print(f"Applied: {applied}")
    print(f"Skipped: {skipped}")
    print(f"Errors : {errors}")


def cmd_ru2en(dry_run: bool, force: bool, folder: Path) -> None:
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        print("Install: pip install deep-translator")
        sys.exit(1)

    MAX_TITLE_LEN = 60
    CHUNK_SIZE = 4500

    def safe_english_filename(text: str) -> str:
        if not text or not text.strip():
            return "Untitled"
        clean = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean[:MAX_TITLE_LEN] if len(clean) > MAX_TITLE_LEN else clean

    def translate_ru_to_en(text: str) -> str:
        if not text or not text.strip():
            return ""
        text = text.strip()
        try:
            if len(text) <= CHUNK_SIZE:
                return GoogleTranslator(source="ru", target="en").translate(text)
            out = []
            for i in range(0, len(text), CHUNK_SIZE):
                chunk = text[i : i + CHUNK_SIZE]
                out.append(GoogleTranslator(source="ru", target="en").translate(chunk))
            return " ".join(out)
        except Exception as e:
            print(f"  [skip translate] {e!r}")
            return text
        finally:
            time.sleep(0.3)

    def parse_md_name(filename: str):
        if not filename.endswith(".md"):
            return None
        m = re.match(r"^(\d+)\.\s*(.+?)\.md\s*$", filename, re.UNICODE)
        if not m:
            return None
        return m.group(1), m.group(2).strip()

    def has_cyrillic(s: str) -> bool:
        return bool(re.search(r"[\u0400-\u04FF]", s))

    if not folder.is_dir():
        print(f"[ERROR] Directory not found: {folder}")
        return

    md_files = [f for f in os.listdir(folder) if f.endswith(".md")]
    print(f"[1] Folder: {folder} ({len(md_files)} .md)")

    renames = []
    skipped_no_match = skipped_no_title = skipped_no_cyrillic = skipped_unchanged = 0
    total_with_cyrillic = 0

    for filename in sorted(md_files, key=lambda x: (len(x), x)):
        parsed = parse_md_name(filename)
        if not parsed:
            skipped_no_match += 1
            continue
        num_str, title_part = parsed
        if not title_part:
            skipped_no_title += 1
            continue
        if not force and not has_cyrillic(title_part):
            skipped_no_cyrillic += 1
            continue
        total_with_cyrillic += 1
        print(f"[3] Translating ({total_with_cyrillic}): {filename[:50]}...")
        en_title = translate_ru_to_en(title_part)
        safe_title = safe_english_filename(en_title)
        new_name = f"{num_str}. {safe_title}.md"
        if new_name == filename:
            skipped_unchanged += 1
            continue
        src = folder / filename
        dst = folder / new_name
        if dst.exists() and src.resolve() != dst.resolve():
            base, ext = os.path.splitext(new_name)
            n = 1
            while (folder / f"{base}_{n}{ext}").exists():
                n += 1
            new_name = f"{base}_{n}{ext}"
            dst = folder / new_name
        renames.append((src, dst, filename, new_name))

    print(
        f"[4] Skip: no match={skipped_no_match}, empty title={skipped_no_title}, "
        f"no Cyrillic={skipped_no_cyrillic}, unchanged={skipped_unchanged}"
    )
    print(f"[5] To rename: {len(renames)}")
    if not renames:
        return
    for i, (src, dst, old_name, new_name) in enumerate(renames, 1):
        print(f"  [{i}/{len(renames)}] {old_name} -> {new_name}")
        if not dry_run:
            try:
                os.rename(src, dst)
            except OSError as e:
                print(f"       Error: {e}")
    print(f"[Done] {len(renames)} {'(dry-run)' if dry_run else 'renamed'}.")


def _prompt(msg: str, default: str = "") -> str:
    tail = f" [{default}]" if default else ""
    s = input(f"{msg}{tail}: ").strip()
    return s if s else default


def interactive_menu() -> None:
    print(
        "\n=== Переименование фанфиков ===\n"
        "1. Предложить имена (Claude) → строки в rename_plan.md\n"
        "2. Применить план (только строки со статусом ✅)\n"
        "3. Перевести RU→EN в именах файлов в папке (по умолчанию Fanfics)\n"
        "0. Выход\n"
    )
    c = _prompt("Выбор", "0")
    if c == "1":
        cmd_suggest()
    elif c == "2":
        cmd_apply()
    elif c == "3":
        fd = _prompt("Папка", str(FANFICS_DIR)) or str(FANFICS_DIR)
        dry = _prompt("Только просмотр? (y/n)", "y").lower() != "n"
        force = _prompt("И --force (и англ. имена)? (y/n)", "n").lower() == "y"
        cmd_ru2en(dry_run=dry, force=force, folder=Path(fd))
    elif c == "0":
        print("Выход.")
    else:
        print("Неизвестный пункт.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("suggest", help="Claude → rename_plan.md")
    sub.add_parser("apply", help="Apply ✅ rows from rename_plan.md")

    p3 = sub.add_parser("ru2en", help="Translate Russian filenames to English")
    p3.add_argument(
        "--folder",
        type=Path,
        default=FANFICS_DIR,
        help="Folder with numbered .md files (default: Fanfics)",
    )
    p3.add_argument("--dry-run", action="store_true")
    p3.add_argument("--force", action="store_true")

    args = parser.parse_args()
    if args.cmd is None:
        interactive_menu()
    elif args.cmd == "suggest":
        cmd_suggest()
    elif args.cmd == "apply":
        cmd_apply()
    elif args.cmd == "ru2en":
        cmd_ru2en(
            dry_run=args.dry_run,
            force=args.force,
            folder=args.folder,
        )


if __name__ == "__main__":
    main()
