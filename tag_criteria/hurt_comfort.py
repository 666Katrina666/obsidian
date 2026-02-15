# -*- coding: utf-8 -*-
"""#hurt-comfort - hurt and comfort (2+ markers, ideally both groups)."""
import re

TAG = "hurt-comfort"

HURT = [
    r"травма", r"травмы", r"травмирован", r"после травмы", r"ранен", r"ранена",
    r"ранение", r"раны", r"боль", r"боли", r"больно", r"причинили боль",
    r"причинить боль", r"залечивать раны", r"залечить рану",
]
COMFORT = [
    r"утешение", r"утешить", r"утешает", r"утешил", r"забота", r"заботиться",
    r"заботятся", r"окружен заботой", r"исцеление", r"исцелить", r"исцеляет",
    r"исцелиться", r"обнял", r"обняли", r"поглаживание", r"поддержка", r"поддержал",
    r"выздоровление", r"оправился", r"прийти в себя", r"hurt-comfort",
    r"ангст с утешением",
]
def check(text):
    if not text:
        return False
    found = set()
    for pat in HURT + COMFORT:
        if re.search(pat, text, re.IGNORECASE):
            found.add(pat)
    return len(found) >= 2
