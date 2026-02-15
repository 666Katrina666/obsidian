# -*- coding: utf-8 -*-
"""#dc/marvel - DC + Marvel crossover (both required)."""
import re

TAG = "dc/marvel"

DC_MARKERS = [
    r"Бэтсемья", r"Бэтпещера", r"Готэм", r"Бэтмен", r"Джейсон", r"Робин",
]
MARVEL_MARKERS = [
    r"Мстители", r"Avengers", r"Старк", r"Тони Старк", r"Iron Man", r"Айрон Мэн",
    r"Марвел", r"Marvel", r"Капитан Америка", r"Captain America", r"Тор", r"Thor",
    r"Халк", r"Hulk", r"Человек-паук", r"Spider-Man", r"Щ\.И\.Т", r"SHIELD",
    r"Наташа", r"Блэк Виддоу", r"Black Widow",
]


def check(text):
    if not text:
        return False
    has_dc = any(re.search(p, text, re.IGNORECASE) for p in DC_MARKERS)
    has_marvel = any(re.search(p, text, re.IGNORECASE) for p in MARVEL_MARKERS)
    return has_dc and has_marvel
