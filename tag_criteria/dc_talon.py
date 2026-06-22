# -*- coding: utf-8 -*-
"""#dc/concept/talon - Court of Owls, Talons.

False-positive notes:
- «талон» without word boundary matches «эталон», «эталонный» (Russian word for
  "standard/benchmark") — fixed with \b prefix on all talон/Talon patterns
- «птичьи черты» (bird features) is too generic — appears in bird-transformation
  fics unrelated to Court of Owls → removed
"""
import re

TAG = "dc/concept/talon"

STRONG = [r"Суд Сов", r"Суда Сов", r"Court of Owls"]
OTHER = [
    r"\bталон",            # talон (any inflection: талона, талоном, талоны...)
    r"Когти Суда",         # Claws of the Court
    r"когти-талоны",
    r"программировали талон",
    r"\bTalon",            # Talon / Talons (EN, word boundary)
]
STRONG_PAT = re.compile("|".join(STRONG), re.IGNORECASE)


def check(text):
    if not text:
        return False
    if STRONG_PAT.search(text):
        return True
    return sum(1 for p in OTHER if re.search(p, text, re.IGNORECASE)) >= 2
