# -*- coding: utf-8 -*-
"""Пакетная подготовка файлов Beta: шапка, описание, переименование.

Использование:
  python Scripts/fanfics/prepare_beta_batch.py --dry-run
  python Scripts/fanfics/prepare_beta_batch.py --apply
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

OBSIDIAN_ROOT = vault_root(__file__)
BETA_DIR = OBSIDIAN_ROOT / "Beta"

HEADER_TEMPLATE = """Теги: 

Описание: 

---
"""

MAX_TITLE_LEN = 72
MAX_DESC_LEN = 320
INVALID_FN = re.compile(r'[<>:"/\\|?*]')

PROMPT_PREFIXES = (
    r"напиши\s+длинную\s+главу\s*\d*\s*:?\s*",
    r"напиши\s+длинную\s+главу\s+",
    r"напиши\s+главу\s*\d*\s*:?\s*",
    r"продолжи\s+следующее\s+до\s+длинной\s+главы\s*",
    r"помоги\s+продумать\s+план\s+глав\s+для\s+ф\s*",
    r"у\s+меня\s+есть\s+идея\.?\s*я\s+дам\s+тебе\s+ее\.?\s*",
    r"вот\s+альтернативный\s+сюжет\s+в\s+кото\s*",
    r"распиши\s+идею\s*(?:про\s+)?",
    r"добавление\s+ссылок\s+на\s+",
)

BAD_TITLE_STARTS = (
    "напиши",
    "продолжи",
    "помоги",
    "у меня",
    "вот ",
    "добав",
    "какая из",
    "1.",
)


def has_tags_header(text: str) -> bool:
    return text.lstrip("\ufeff").lstrip().lower().startswith("теги:")


def parse_file_number(name: str) -> int | None:
    m = re.match(r"^(\d+)", name)
    return int(m.group(1)) if m else None


def body_after_header(text: str) -> str:
    if not has_tags_header(text):
        return text
    if "---" in text:
        return text.split("---", 1)[1]
    lines = text.splitlines()
    if len(lines) > 1:
        return "\n".join(lines[1:])
    return ""


def extract_prompt(body: str) -> str:
    m = re.search(r"\*\*Вы:\*\*\s*\n(.*?)(?:\n\*\*Ассистент:\*\*|\Z)", body, re.DOTALL | re.I)
    if m:
        return m.group(1).strip()
    chunks: list[str] = []
    for line in body.splitlines():
        s = line.strip()
        if not s:
            if chunks and len(" ".join(chunks)) > 80:
                break
            continue
        if s.startswith("##") and chunks:
            break
        if s.lower().startswith("думал на протяжении"):
            break
        chunks.append(s)
        if len(" ".join(chunks)) > 1200:
            break
    return " ".join(chunks).strip()


def clean_title_piece(s: str) -> str:
    s = s.strip().strip('"«»**')
    s = re.sub(r"\s+", " ", s)
    s = INVALID_FN.sub(" ", s)
    return s.strip(" .-")


def shorten_title(s: str, max_len: int = MAX_TITLE_LEN) -> str:
    s = clean_title_piece(s)
    if len(s) <= max_len:
        return s
    cut = s[: max_len - 1].rsplit(" ", 1)[0]
    return (cut or s[: max_len - 1]).strip() + "…"


def title_from_body(body: str) -> str | None:
    block = re.search(
        r"##\s*Рабочее название\s*\n+(.*?)(?:\n##|\n---|\Z)",
        body,
        re.I | re.S,
    )
    if block:
        for line in block.group(1).splitlines():
            t = clean_title_piece(re.sub(r"^\*+|\*+$", "", line))
            t = t.strip("«»\"'")
            if len(t) >= 6 and not t.lower().startswith("или "):
                return shorten_title(t)
    for pat in (
        r"\*\*«([^»]+)»\*\*",
        r"#+\s*Глава[:\s]+([^\n]+)",
        r"##\s*Глава[:\s]+([^\n]+)",
    ):
        m = re.search(pat, body, re.I)
        if m:
            t = clean_title_piece(m.group(1))
            if len(t) >= 8:
                return shorten_title(t)
    return None


def polish_title_candidate(title: str) -> str:
    t = clean_title_piece(title)
    t = re.sub(r"^\[\s*", "", t)
    for pref in (
        "идея про овервотч",
        "идея про overwatch",
        "идея au по overwatch",
        "часть идеи, а ты ее подробно распиши",
        "помоги продумать фанфик описание",
        "пропиши идею",
        "проработай мир фанфика про бэтсемью",
        "напиши длинной главой",
        "длинная глава",
        "длинная глава ",
        "глава ",
    ):
        if t.lower().startswith(pref):
            t = t[len(pref) :].strip(" .:—-")
    return shorten_title(t) if t else title


def title_from_prompt(prompt: str) -> str | None:
    if not prompt:
        return None
    p = prompt
    for pref in PROMPT_PREFIXES:
        p = re.sub(pref, "", p, flags=re.I)
    p = p.strip()
    # первая фраза до точки/переноса
    m = re.match(r"^(.{20,200}?)(?:\.|$)", p, re.DOTALL)
    chunk = (m.group(1) if m else p[:200]).replace("\n", " ")
    chunk = re.sub(r"\s+", " ", chunk).strip()
    if len(chunk) < 12:
        return None
    return shorten_title(chunk)


def make_description(prompt: str, body: str) -> str:
    src = prompt or body
    src = re.sub(r"\*\*[^*]+\*\*", "", src)
    src = re.sub(r"\s+", " ", src).strip()
    if not src:
        return ""
    # первая осмысленная фраза
    parts = re.split(r"(?<=[.!?])\s+", src)
    out: list[str] = []
    for part in parts:
        part = part.strip()
        if len(part) < 15:
            continue
        low = part.lower()
        if low.startswith(BAD_TITLE_STARTS):
            continue
        if any(
            low.startswith(x)
            for x in (
                "я дам тебе",
                "распиши идею",
                "не надо продумывать",
                "у меня есть идея",
            )
        ):
            continue
        out.append(part)
        if len(" ".join(out)) >= 120:
            break
    desc = " ".join(out) if out else src[:MAX_DESC_LEN]
    if len(desc) > MAX_DESC_LEN:
        desc = desc[: MAX_DESC_LEN - 1].rsplit(" ", 1)[0] + "…"
    return desc


def needs_polish_rename(name: str) -> bool:
    """Переименовать даже если формат N. Title ок, но заголовок «сырой»."""
    m = re.match(r"^(\d+)\.\s*(.+)\.md$", name)
    if not m:
        return True
    title = m.group(2).lower()
    markers = (
        "идея про",
        "часть идеи",
        "помоги продумать",
        "[ ",
        "[пр",
        "напиши ",
        "длинная глава",
        "длинной главой",
        "пропиши идею",
        "проработай",
        "овервотч (имей",
        "# список",
        "анфика (глав",
    )
    return any(x in title for x in markers)


def needs_rename(name: str) -> bool:
    if name.endswith("..md") or re.match(r"^\d+\.md$", name):
        return True
    m = re.match(r"^(\d+)\.\s*(.+)\.md$", name)
    if not m:
        return True
    title = m.group(2).strip().lower()
    if len(title) < 8 or title.endswith("."):
        return True
    return any(title.startswith(x) for x in BAD_TITLE_STARTS)


def suggest_filename(num: int, text: str, old_name: str) -> str | None:
    body = body_after_header(text)
    prompt = extract_prompt(body)
    title = title_from_body(body) or title_from_prompt(prompt)
    if title:
        title = polish_title_candidate(title)
    if title and any(title.lower().startswith(x) for x in BAD_TITLE_STARTS):
        title = title_from_body(body) or polish_title_candidate(title_from_prompt(prompt) or "")
    if not title:
        m = re.match(r"^(\d+)\.\s*(.+)\.md$", old_name)
        if m and not needs_rename(old_name):
            return None
        title = shorten_title(prompt[:60] if prompt else f"Черновик {num}")
    new_name = f"{num}. {title}.md"
    if new_name == old_name:
        return None
    return new_name


def existing_description(text: str) -> str:
    for line in text.splitlines()[:12]:
        if line.lower().startswith("описание:"):
            return line.split(":", 1)[1].strip()
    return ""


def update_header_block(text: str, description: str) -> str:
    if not has_tags_header(text):
        text = HEADER_TEMPLATE + text.lstrip("\ufeff")
    lines = text.splitlines()
    if not lines:
        return HEADER_TEMPLATE
    # теги — строка 0
    desc_line_idx = None
    sep_idx = None
    for i, line in enumerate(lines):
        if line.lower().startswith("описание:"):
            desc_line_idx = i
        if line.strip() == "---" and desc_line_idx is not None and i > desc_line_idx:
            sep_idx = i
            break
    if desc_line_idx is None:
        # вставить описание после тегов
        new_lines = [lines[0], "", f"Описание: {description}", "", "---"]
        rest_start = 1
        if len(lines) > 1 and lines[1].strip() == "":
            rest_start = 2
        if len(lines) > rest_start and lines[rest_start].strip() == "---":
            rest_start += 1
            if rest_start < len(lines) and lines[rest_start].strip() == "":
                rest_start += 1
        return "\n".join(new_lines + lines[rest_start:]) + ("\n" if text.endswith("\n") else "")
    if description:
        lines[desc_line_idx] = f"Описание: {description}"
    if sep_idx is None:
        lines.insert(desc_line_idx + 1, "")
        lines.insert(desc_line_idx + 2, "---")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def process_file(path: Path, apply: bool) -> dict:
    info = {"file": path.name, "header": False, "desc": False, "rename": None, "skip": None}
    if path.stat().st_size == 0:
        info["skip"] = "пустой файл"
        return info
    text = path.read_text(encoding="utf-8")
    num = parse_file_number(path.name)
    if num is None:
        info["skip"] = "нет номера в имени"
        return info

    changed = False
    if not has_tags_header(text):
        text = HEADER_TEMPLATE + text.lstrip("\ufeff")
        info["header"] = True
        changed = True

    body = body_after_header(text)
    prompt = extract_prompt(body)
    desc = make_description(prompt, body)
    if desc and not existing_description(text):
        text = update_header_block(text, desc)
        info["desc"] = True
        changed = True

    if needs_rename(path.name) or needs_polish_rename(path.name):
        new_name = suggest_filename(num, text, path.name)
    else:
        new_name = None
    if new_name and new_name != path.name:
        info["rename"] = new_name

    if apply:
        if changed:
            path.write_text(text, encoding="utf-8")
        if new_name:
            dest = path.parent / new_name
            if dest.exists() and dest.resolve() != path.resolve():
                info["skip"] = f"конфликт: {new_name}"
                info["rename"] = None
            else:
                path.rename(dest)
                info["file"] = new_name

    return info


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="Записать изменения")
    ap.add_argument("--dry-run", action="store_true", help="Только показать план")
    args = ap.parse_args()
    apply = args.apply and not args.dry_run
    if not args.apply and not args.dry_run:
        ap.print_help()
        return

    files = sorted(BETA_DIR.glob("*.md"))
    stats = {"header": 0, "desc": 0, "rename": 0, "skip": 0}
    for path in files:
        info = process_file(path, apply)
        flags = []
        if info.get("header"):
            flags.append("шапка")
            stats["header"] += 1
        if info.get("desc"):
            flags.append("описание")
            stats["desc"] += 1
        if info.get("rename"):
            flags.append(f"-> {info['rename']}")
            stats["rename"] += 1
        if info.get("skip"):
            flags.append(f"SKIP: {info['skip']}")
            stats["skip"] += 1
        if flags:
            print(f"{info['file']}: {', '.join(flags)}")

    mode = "ПРИМЕНЕНО" if apply else "DRY-RUN"
    print(f"\n{mode}: шапок {stats['header']}, описаний {stats['desc']}, переименований {stats['rename']}, пропусков {stats['skip']}")
    if not apply:
        print("Запустите с --apply для записи.")


if __name__ == "__main__":
    main()
