# -*- coding: utf-8 -*-
"""#dc - DC Comics / Batfamily."""
import re

import _common

TAG = "dc"

DC_MARKERS = [
    r"Бэтпещера", r"Бэт-пещера", r"Бэтсемья", r"Бэт-семья",
    r"Готэм", r"Бэтмен", r"Брюс", r"Джейсон Тодд", r"Дик Грейсон",
    r"Робин", r"Красный Капюшон", r"Найтвинг", r"Дамиан", r"Тим Дрейк",
    r"Барбара", r"Оракул", r"Альфред", r"Бэтмобиль",
]


def check(text):
    if not text:
        return False
    return _common.count_distinct(DC_MARKERS, text) >= 2
