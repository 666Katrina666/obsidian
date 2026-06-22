# -*- coding: utf-8 -*-
"""Подставить ручные описания в Beta (кроме 819.md — только шаблон)."""
from __future__ import annotations

import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
from paths import vault_root

from beta_descriptions import DESCRIPTIONS, TEMPLATE_819

BETA = vault_root(__file__) / "Beta"


def set_description(text: str, desc: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    i = 0
    if i < len(lines) and lines[i].lower().startswith("теги:"):
        out.append(lines[i])
        out.append("")
        i += 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    out.append(f"Описание: {desc}")
    out.append("")
    while i < len(lines):
        if lines[i].lower().startswith("описание:"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("---") and lines[i].strip() != "---":
                if lines[i].strip() == "---":
                    break
                i += 1
            continue
        if lines[i].strip() == "---":
            out.append("---")
            i += 1
            break
        i += 1
    out.extend(lines[i:])
    result = "\n".join(out)
    if text.endswith("\n"):
        result += "\n"
    return result


def file_number(name: str) -> int | None:
    m = re.match(r"^(\d+)", name)
    return int(m.group(1)) if m else None


def main() -> None:
    updated = 0
    for path in sorted(BETA.glob("*.md")):
        if path.name == "819.md":
            path.write_text(TEMPLATE_819, encoding="utf-8")
            print("819.md — пустой шаблон")
            continue
        num = file_number(path.name)
        if num is None or num not in DESCRIPTIONS:
            print(f"SKIP (нет описания): {path.name}")
            continue
        text = path.read_text(encoding="utf-8")
        new_text = set_description(text, DESCRIPTIONS[num])
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            updated += 1
    print(f"Обновлено описаний: {updated}")


if __name__ == "__main__":
    main()
