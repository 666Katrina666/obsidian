# -*- coding: utf-8 -*-
"""#dc/dp - DC + Danny Phantom crossover (both required).

False-positive notes:
- «призрак» / «призраки» are common Russian words used as ghost metaphors in DC fics → removed
- «Дэнни» is a common first name unrelated to Danny Phantom → removed; use full «Дэнни Фантом»
- Remaining markers are specific to the DP universe; 1+ is enough to confirm crossover
"""
import re

TAG = "dc/dp"

DC_MARKERS = [
    r"Бэтсемья", r"Бэт-семья", r"Бэтпещера", r"Готэм", r"Бэтмен", r"Джейсон",
    r"Дик", r"Робин", r"Красный Капюшон",
]
# Only DP-specific markers; generic «призрак», «призраки», «Дэнни» removed
DP_MARKERS = [
    r"халфа",            # halfa (half-ghost) — DP-specific term
    r"полупризрак",      # half-ghost
    r"призрачная зона",  # Ghost Zone
    r"Ghost Zone",
    r"эктоплазм",        # ectoplasm (covers эктоплазма, эктоплазмой, etc.)
    r"Дэнни Фантом",     # Danny Phantom (full name)
    r"GIW",              # Guys in White (DP agency)
    r"Фентон",           # Fenton (surname of Danny's family)
    r"призрачная форм",  # ghost form (covers all inflections)
    r"ядро призрака",    # ghost core — very DP-specific
]


def check(text):
    if not text:
        return False
    has_dc = any(re.search(p, text, re.IGNORECASE) for p in DC_MARKERS)
    if not has_dc:
        return False
    return any(re.search(p, text, re.IGNORECASE) for p in DP_MARKERS)
