# -*- coding: utf-8 -*-
"""#ABO - Alpha/Beta/Omega dynamics."""
import re

TAG = "ABO"

EXPLICIT = [r"ABO", r"a/b/o", r"омега-верс", r"omega verse", r"платонический ABO", r"платонический або"]
EXPLICIT_PAT = re.compile("|".join(EXPLICIT), re.IGNORECASE)

MARKERS = [
    r"альфа", r"альфы", r"альфа-самец", r"омега", r"омеги", r"бета", r"беты",
    r"динамика альфа", r"альфа и омега", r"гнездо", r"гнездовани", r"течка",
    r"течку", r"период течки", r"метка", r"метить", r"пометил", r"запах омеги",
]


def check(text):
    if not text:
        return False
    if EXPLICIT_PAT.search(text):
        return True
    found = set()
    for pat in MARKERS:
        if re.search(pat, text, re.IGNORECASE):
            found.add(pat)
    return len(found) >= 2
