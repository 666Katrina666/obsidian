# -*- coding: utf-8 -*-
"""#dragon - dragons and dragon transformations. Require 2+ markers."""
import re

TAG = "dragon"

PATTERNS = [
    r"дракон", r"драконий", r"драконья", r"драконье",
    r"превратился в дракона", r"превращается в дракона", r"драконья форма",
    r"в облике дракона", r"драконий облик", r"драконья чешуя", r"драконьи крылья",
    r"полудракон", r"полу-дракон", r"драконья трансформация", r"драконья природа",
    r"дракон-оборотень", r"оборотень-дракон",
]


def check(text):
    if not text:
        return False
    found = set()
    for p in PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            found.add(p)
    return len(found) >= 2
