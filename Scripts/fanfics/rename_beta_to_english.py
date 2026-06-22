# -*- coding: utf-8 -*-
"""Rename Beta/*.md to English titles (Fanfics-style: N. Title - subtitle.md).

  python Scripts/fanfics/rename_beta_to_english.py --dry-run
  python Scripts/fanfics/rename_beta_to_english.py --apply
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

_SCRIPTS_FANFICS = Path(__file__).resolve().parent
if str(_SCRIPTS_FANFICS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_FANFICS))

from beta_english_titles import KEEP_PLAIN, TITLES
from prepare_beta_batch import (
    body_after_header,
    clean_title_piece,
    extract_prompt,
    polish_title_candidate,
    shorten_title,
    title_from_body,
    title_from_prompt,
)

OBSIDIAN_ROOT = vault_root(__file__)
BETA_DIR = OBSIDIAN_ROOT / "Beta"
MAX_FILENAME_LEN = 105
INVALID_FN = re.compile(r'[<>:"/\\|?*]')
# From this number onward: filename is only ``814..md`` (no English title).
NUMBER_ONLY_FROM = 814


def parse_file_ref(name: str) -> tuple[int, float | None] | None:
    """Return (base_num, sub_index) e.g. 880.3 from '880 3.md' or '880..md'."""
    m = re.match(r"^(\d+)\s+(\d+)\.md$", name)
    if m:
        return int(m.group(1)), float(int(m.group(2)))
    m = re.match(r"^(\d+)\.\.md$", name)
    if m:
        return int(m.group(1)), None
    m = re.match(r"^(\d+)\.md$", name)
    if m:
        return int(m.group(1)), None
    m = re.match(r"^(\d+)\.\s", name)
    if m:
        return int(m.group(1)), None
    return None


def format_num(base: int, sub: float | None) -> str:
    if sub is None:
        return str(base)
    if sub == int(sub):
        return f"{base}.{int(sub)}"
    return f"{base}.{sub}"


def safe_english_filename(text: str) -> str:
    text = clean_title_piece(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def translate_ru_to_en(text: str) -> str:
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        return text
    text = text.strip()
    if not text or not re.search(r"[\u0400-\u04FF]", text):
        return text
    try:
        if len(text) <= 450:
            return GoogleTranslator(source="ru", target="en").translate(text)
        out: list[str] = []
        chunk = 400
        for i in range(0, len(text), chunk):
            part = text[i : i + chunk]
            out.append(GoogleTranslator(source="ru", target="en").translate(part))
            time.sleep(0.25)
        return " ".join(out)
    except Exception as e:
        print(f"  [translate skip] {e!r}")
        return text


def suggest_title_from_content(path: Path) -> str:
    if path.stat().st_size == 0:
        return "Draft Placeholder"
    text = path.read_text(encoding="utf-8")
    body = body_after_header(text)
    prompt = extract_prompt(body)
    title = title_from_prompt(prompt) or title_from_body(body)
    if title:
        title = polish_title_candidate(title)
    if not title:
        prompt = extract_prompt(body) or body.strip()[:500]
        prompt = re.sub(
            r"^(напиши|помоги|вот у меня|идея|длинная глава)\b[^.]*[.:]\s*",
            "",
            prompt,
            flags=re.I,
        )
        title = shorten_title(prompt[:200] if prompt else "Draft")
    if re.search(r"[\u0400-\u04FF]", title):
        title = translate_ru_to_en(title)
    return safe_english_filename(title) or "Draft"


def target_name(path: Path) -> str | None:
    ref = parse_file_ref(path.name)
    if ref is None:
        return None
    base, sub = ref
    num_label = format_num(base, sub)

    if base in KEEP_PLAIN and sub is None:
        return "819.md"

    if base >= NUMBER_ONLY_FROM:
        if sub is not None:
            return f"{base} {int(sub)}..md"
        return f"{base}..md"

    if path.stat().st_size == 0:
        if base == 880 and sub is not None:
            return f"880.{int(sub)}. Draft Slot {int(sub)}.md"
        if base == 890:
            return "890. Draft Placeholder.md"
        return f"{num_label}. Draft Placeholder.md"

    if base in TITLES and sub is None:
        title = TITLES[base]
    elif base == 880 and sub is not None:
        title = f"Draft Slot {int(sub)}"
    else:
        title = suggest_title_from_content(path)

    title = safe_english_filename(title)
    new_name = f"{num_label}. {title}.md"
    if len(new_name) > MAX_FILENAME_LEN:
        allowed = MAX_FILENAME_LEN - len(".md") - len(num_label) - 2
        if allowed < 12:
            new_name = f"{num_label}.md"
        else:
            title = title[: allowed - 1].rsplit(" ", 1)[0] + "…"
            new_name = f"{num_label}. {title}.md"
    return new_name


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--dry-run", action="store_true", default=True)
    args = ap.parse_args()
    apply = args.apply
    dry = not apply

    moves: list[tuple[Path, Path]] = []
    for path in sorted(BETA_DIR.glob("*.md"), key=lambda p: p.name.lower()):
        new_name = target_name(path)
        if not new_name or new_name == path.name:
            continue
        dest = BETA_DIR / new_name
        if dest.exists() and dest.resolve() != path.resolve():
            stem, ext = dest.stem, dest.suffix
            n = 2
            while (BETA_DIR / f"{stem}_{n}{ext}").exists():
                n += 1
            dest = BETA_DIR / f"{stem}_{n}{ext}"
            new_name = dest.name
        moves.append((path, dest))

    print(f"Beta rename: {len(moves)} files ({'apply' if apply else 'dry-run'})")
    for src, dst in moves:
        print(f"  {src.name}")
        print(f"    -> {dst.name}")
        if apply:
            src.rename(dst)

    if apply:
        print("Done.")
    else:
        print("Use --apply to rename.")


if __name__ == "__main__":
    main()
