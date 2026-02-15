# -*- coding: utf-8 -*-
"""#dc/bnha - DC + My Hero Academia crossover (both required)."""
import re

TAG = "dc/bnha"

DC_MARKERS = [
    r"Бэтсемья", r"Бэтпещера", r"Готэм", r"Бэтмен", r"Джейсон", r"Робин",
]
BNHA_MARKERS = [
    r"квирки", r"квирк", r"MHA", r"My Hero Academia", r"герой академия",
    r"Боку но Хиро", r"UA", r"Юэй", r"Юей", r"Олл Майт", r"All Might",
    r"Изуку", r"Деку", r"геройская академия", r"академия героев",
]


def check(text):
    if not text:
        return False
    has_dc = any(re.search(p, text, re.IGNORECASE) for p in DC_MARKERS)
    has_bnha = any(re.search(p, text, re.IGNORECASE) for p in BNHA_MARKERS)
    return has_dc and has_bnha
