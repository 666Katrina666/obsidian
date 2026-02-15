# -*- coding: utf-8 -*-
"""#transformation - character transformations."""
import re

TAG = "transformation"

PATTERNS = [
    r"трансформ", r"превращ", r"превращается в", r"превратился в",
    r"меняет облик", r"изменил облик", r"смена формы", r"облик изменился",
    r"форма изменилась", r"новый облик", r"другая форма", r"перевоплощение",
    r"меняет форму", r"меняет тело",
]
PAT = re.compile("|".join(PATTERNS), re.IGNORECASE)


def check(text):
    return bool(text and PAT.search(text))
