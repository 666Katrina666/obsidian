# -*- coding: utf-8 -*-
"""#dc/concept/talon - Court of Owls, Talons.

False-positive notes:
- «талон» without word boundary matches «эталон», «эталонный» (Russian word for
  "standard/benchmark") — fixed with \b prefix on all talон/Talon patterns
- «птичьи черты» (bird features) is too generic — appears in bird-transformation
  fics unrelated to Court of Owls → removed
- Talon is also the terrorist organisation of Overwatch: «Shimada Brothers
  Escape Talon» (1042) and 772.2 matched on «Talon» + «талон» with no DC at
  all. Like every other dc/* tag, this one now requires a DC marker (29.10.2026).
"""
import re

import _common

DC_MARKERS = ["Бэтсемья", "Бэтпещера", "Готэм", "Бэтмен", "Джейсон", "Робин", "Брюс"]

TAG = "dc/concept/talon"

STRONG = [r"Суд Сов", r"Суда Сов", r"Court of Owls"]
OTHER = [
    r"\bталон",            # talон (any inflection: талона, талоном, талоны...)
    r"Когти Суда",         # Claws of the Court
    r"когти-талоны",
    r"программировали талон",
    r"\bTalon",            # Talon / Talons (EN, word boundary)
]
STRONG_PAT = _common.compile_any(STRONG)


def check(text):
    if not text:
        return False
    if not _common.search_any(DC_MARKERS, text):
        return False
    if STRONG_PAT.search(text):
        return True
    return _common.count_distinct(OTHER, text) >= 2
