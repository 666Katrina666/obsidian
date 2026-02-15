# -*- coding: utf-8 -*-
"""Rename .md files from Russian titles to English (translated).
Keeps leading "NN. " prefix. Handles typos via translation. Use --dry-run to preview.
"""
import argparse
import os
import re
import sys
import time

try:
    from deep_translator import GoogleTranslator
except ImportError:
    print("Install: pip install deep-translator")
    sys.exit(1)

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
MAX_TITLE_LEN = 60
# Google Translate limit per request
CHUNK_SIZE = 4500


def safe_english_filename(text):
    """Keep letters, digits, spaces, hyphen; collapse spaces; limit length."""
    if not text or not text.strip():
        return "Untitled"
    clean = re.sub(r"[^\w\s\-]", " ", text, flags=re.UNICODE)
    clean = re.sub(r"\s+", " ", clean).strip()
    return clean[:MAX_TITLE_LEN] if len(clean) > MAX_TITLE_LEN else clean


def translate_ru_to_en(text):
    """Translate Russian to English. Returns original on failure."""
    if not text or not text.strip():
        return ""
    text = text.strip()
    try:
        if len(text) <= CHUNK_SIZE:
            return GoogleTranslator(source="ru", target="en").translate(text)
        # Long text: translate in chunks and join
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


def parse_md_name(filename):
    """Return (number_str, rest) or None. E.g. '01. Some title.md' -> ('01', 'Some title')."""
    if not filename.endswith(".md"):
        return None
    m = re.match(r"^(\d+)\.\s*(.+?)\.md\s*$", filename, re.UNICODE)
    if not m:
        return None
    return m.group(1), m.group(2).strip()


def has_cyrillic(s):
    return bool(re.search(r"[\u0400-\u04FF]", s))


def main():
    ap = argparse.ArgumentParser(description="Rename Russian .md filenames to English")
    ap.add_argument("--dry-run", action="store_true", help="Only print renames, do not rename")
    ap.add_argument("--force", action="store_true", help="Translate even if title looks already English")
    args = ap.parse_args()

    print(f"[1] Script started. Directory: {OUT_DIR}")

    if not os.path.isdir(OUT_DIR):
        print(f"[ERROR] Directory not found: {OUT_DIR}")
        return

    md_files = [f for f in os.listdir(OUT_DIR) if f.endswith(".md")]
    print(f"[2] Found {len(md_files)} .md files in folder")

    renames = []
    skipped_no_match = 0
    skipped_no_title = 0
    skipped_no_cyrillic = 0
    skipped_unchanged = 0
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
        if not args.force and not has_cyrillic(title_part):
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
        src = os.path.join(OUT_DIR, filename)
        dst = os.path.join(OUT_DIR, new_name)
        if os.path.exists(dst) and os.path.abspath(src) != os.path.abspath(dst):
            base, ext = os.path.splitext(new_name)
            n = 1
            while os.path.exists(os.path.join(OUT_DIR, f"{base}_{n}{ext}")):
                n += 1
            new_name = f"{base}_{n}{ext}"
            dst = os.path.join(OUT_DIR, new_name)
        renames.append((src, dst, filename, new_name))

    print(f"[4] Skip reasons: no 'NN. title.md' match={skipped_no_match}, empty title={skipped_no_title}, no Cyrillic={skipped_no_cyrillic}, unchanged after translate={skipped_unchanged}")
    print(f"[5] Files to rename (with Russian): {len(renames)}")

    if not renames:
        print("[6] No files to rename. If you expected Russian names, check: (1) filename format 'NN. Title.md', (2) use --force to process English names too.")
        return

    for i, (src, dst, old_name, new_name) in enumerate(renames, 1):
        print(f"  [{i}/{len(renames)}] {old_name}")
        print(f"       -> {new_name}")
        if not args.dry_run:
            try:
                os.rename(src, dst)
            except OSError as e:
                print(f"       Error: {e}")
    print(f"[Done] {len(renames)} file(s) {'(dry-run, no changes)' if args.dry_run else 'renamed'}.")


if __name__ == "__main__":
    main()
