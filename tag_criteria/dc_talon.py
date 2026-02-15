# -*- coding: utf-8 -*-
"""#dc/concept/talon - Court of Owls, Talons."""
import re

TAG = "dc/concept/talon"

STRONG = [r"Суд Сов", r"Суда Сов", r"Court of Owls"]
OTHER = [
    r"талон", r"талоны", r"Талон", r"Когти Суда", r"когти-талоны",
    r"программировали талон", r"птичьи черты", r"Talon", r"Talons",
]
STRONG_PAT = re.compile("|".join(STRONG), re.IGNORECASE)
OTHER_PAT = re.compile("|".join(OTHER), re.IGNORECASE)


def check(text):
    if not text:
        return False
    if STRONG_PAT.search(text):
        return True
    return sum(1 for p in OTHER if re.search(p, text, re.IGNORECASE)) >= 2
