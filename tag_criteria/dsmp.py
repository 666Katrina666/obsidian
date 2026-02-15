# -*- coding: utf-8 -*-
"""#dsmp - Dream SMP."""
import re

TAG = "dsmp"

EXPLICIT = [r"Dream SMP", r"Дрим СМП", r"ДримСМП", r"DSMP", r"L'Manberg", r"Л'Манберг", r"Ламанберг"]
CHARACTERS = [
    r"Георг", r"СапНап", r"Томми", r"Туббо", r"Вилбур", r"Техно", r"Филза", r"Ранбу",
]
EXPLICIT_PAT = re.compile("|".join(EXPLICIT), re.IGNORECASE)
CHAR_PAT = re.compile("|".join(CHARACTERS), re.IGNORECASE)


def check(text):
    if not text:
        return False
    if EXPLICIT_PAT.search(text):
        return True
    char_matches = CHAR_PAT.findall(text)
    return len(char_matches) >= 2
