# -*- coding: utf-8 -*-
"""#dc/concept/dark_Bruce - dark/evil Bruce AU."""
import re

import _common

TAG = "dc/concept/dark_Bruce"

STRONG = [
    r"темный Брюс", r"тёмный Брюс", r"Брюс злодей", r"Брюс похитил",
]
MARKERS = [
    r"злой Брюс", r"Брюс — злодей", r"Брюс тиран", r"Брюс сошёл с ума",
    r"безумный Брюс", r"одержимый Брюс", r"Брюс похищает", r"Брюс заставляет",
    r"Брюс запрещает", r"контроль Брюса", r"Брюс контролирует",
]
STRONG_PAT = _common.compile_any(STRONG)
MARKERS_PAT = _common.compile_any(MARKERS)


def check(text):
    if not text:
        return False
    if STRONG_PAT.search(text):
        return True
    found = _common.count_distinct(MARKERS, text)
    return found >= 2
