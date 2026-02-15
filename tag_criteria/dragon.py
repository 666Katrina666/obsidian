# -*- coding: utf-8 -*-
"""#dragon - dragons and dragon transformations."""
import re

TAG = "dragon"

PATTERNS = [
    r"дракон", r"драконий", r"драконья", r"драконье",
    r"превратился в дракона", r"превращается в дракона", r"драконья форма",
    r"в облике дракона", r"драконий облик", r"драконья чешуя", r"драконьи крылья",
    r"полудракон", r"полу-дракон", r"драконья трансформация", r"драконья природа",
    r"дракон-оборотень", r"оборотень-дракон",
]
PAT = re.compile("|".join(PATTERNS), re.IGNORECASE)


def check(text):
    return bool(text and PAT.search(text))
