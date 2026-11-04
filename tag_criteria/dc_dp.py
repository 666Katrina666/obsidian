# -*- coding: utf-8 -*-
"""#dc/dp - DC + Danny Phantom crossover (both required).

False-positive notes:
- «призрак» / «призраки» are common Russian words used as ghost metaphors in DC fics → removed
- «Дэнни» is a common first name unrelated to Danny Phantom → removed; use full «Дэнни Фантом»
- Remaining markers are specific to the DP universe; 1+ is enough to confirm crossover
"""
import re

import _common

TAG = "dc/dp"

DC_MARKERS = [
    r"Бэтсемья", r"Бэт-семья", r"Бэтпещера", r"Готэм", r"Бэтмен", r"Джейсон",
    r"Дик", r"Робин", r"Красный Капюшон",
]
# Only DP-specific markers; generic «призрак», «призраки», «Дэнни» removed.
# Одного такого маркера достаточно: вне кроссовера они не встречаются.
STRONG_MARKERS = [
    r"халфа",            # halfa (half-ghost) — DP-specific term
    r"halfa",            # то же латиницей: у 202 термин только в таком виде
    r"полупризрак",      # half-ghost
    r"призрачная зона",  # Ghost Zone
    r"Ghost Zone",
    r"Дэнни Фантом",     # Danny Phantom (full name)
    r"GIW",              # Guys in White (DP agency)
    r"Фентон",           # Fenton (surname of Danny's family)
    r"ядро призрака",    # ghost core — very DP-specific
]

# Слабые: термин из DP, но живёт и сам по себе в любом фанфике про призраков.
# Разовое упоминание тега не даёт (14.08.2026). Проверено по всему хранилищу:
# у шести ложных срабатываний слабый маркер встречается РОВНО ОДИН раз —
# «сигнатура, похожая на эктоплазму» (513.2), «ближе к эктоплазменным
# паразитам» (629.1), «плюнет в меня эктоплазмой» (783), призрачная форма
# Стеф (487) и семья, ставшая призраками в Undertale (642.1). У настоящих
# кроссоверов те же слова звучат от двух до тринадцати раз, поэтому порог
# по числу вхождений, а не по числу разных маркеров: «два разных» снимало
# тег с 202, 341 и других, где термин один, но он и есть тема заметки.
WEAK_MARKERS = [
    r"эктоплазм",        # ectoplasm (covers эктоплазма, эктоплазмой, etc.)
    r"призрачная форм",  # ghost form (covers all inflections)
]
WEAK_MIN = 2

DP_MARKERS = STRONG_MARKERS + WEAK_MARKERS


def check(text):
    if not text:
        return False
    if not _common.search_any(DC_MARKERS, text):
        return False
    if _common.search_any(STRONG_MARKERS, text):
        return True
    return _common.count_occurrences(WEAK_MARKERS, text) >= WEAK_MIN
