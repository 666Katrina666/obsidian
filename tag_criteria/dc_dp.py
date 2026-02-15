# -*- coding: utf-8 -*-
"""#dc/dp - DC + Danny Phantom crossover (both required)."""
import re

TAG = "dc/dp"

DC_MARKERS = [
    r"Бэтсемья", r"Бэт-семья", r"Бэтпещера", r"Готэм", r"Бэтмен", r"Джейсон",
    r"Дик", r"Робин", r"Красный Капюшон",
]
DP_MARKERS = [
    r"халфа", r"полупризрак", r"призрачная зона", r"Ghost Zone", r"эктоплазма",
    r"эктоплазм", r"Дэнни Фантом", r"Дэнни", r"GIW", r"призрак", r"призраки",
    r"Фентон", r"призрачная форма", r"ядро призрака",
]


def check(text):
    if not text:
        return False
    has_dc = any(re.search(p, text, re.IGNORECASE) for p in DC_MARKERS)
    dp_count = sum(1 for p in DP_MARKERS if re.search(p, text, re.IGNORECASE))
    return has_dc and dp_count >= 2
