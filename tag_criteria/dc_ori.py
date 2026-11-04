# -*- coding: utf-8 -*-
"""#dc/ori - кроссовер DC с Ori (Blind Forest / Will of the Wisps).

Нужны обе вселенные: DC и Ori. Одного «духа света» мало — это общий
фэнтезийный оборот, поэтому он в слабых и требует пары.
"""
import re

import _common

TAG = "dc/ori"

DC_MARKERS = ["Бэтсемья", "Бэтпещера", "Готэм", "Бэтмен", "Джейсон", "Робин", "Брюс"]

# Названия игр и уникальная топонимика — по одному достаточно.
ORI_STRONG = [
    r"Ori and the",
    r"Blind Forest",
    r"Will of the Wisps",
    r"Нибел\w*",          # Нибель, Нибелю — лес из первой части
    r"[Дд]рево\s+[Дд]ухов",
    r"[Дд]ух[а-я]*\s+[Дд]ерев",
]

# Имена и существа: поодиночке слишком коротки, нужны два разных.
ORI_OTHER = [
    r"\bOri\b",
    r"\bОри\b",
    r"\bКуро\b",          # сова
    r"\bСейн\b",          # светящийся спутник
    r"\bГумо\b",
    r"гумон\w*",
    r"\bНару\b",
    r"гор[аеуы]\s+Хору",
    r"[Дд]ух[а-я]*\s+[Сс]вета",
]


def check(text):
    if not text:
        return False
    if not _common.search_any(DC_MARKERS, text):
        return False
    if _common.search_any(ORI_STRONG, text):
        return True
    return _common.count_distinct(ORI_OTHER, text) >= 2
