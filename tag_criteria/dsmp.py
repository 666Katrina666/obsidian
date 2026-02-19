# -*- coding: utf-8 -*-
"""#dsmp - Dream SMP. Only if text is clearly set in DSMP universe."""
import re

TAG = "dsmp"

EXPLICIT = [
    r"Dream SMP", r"Дрим СМП", r"ДримСМП", r"DSMP",
    r"L'Manberg", r"Л'Манберг", r"Ламанберг",
    r"сервер.*Дрим|Дрим.*сервер", r"вселенн.*DSMP|DSMP.*вселенн",
]
CHARACTERS = [
    r"Георг", r"СапНап", r"Томми", r"Туббо", r"Вилбур", r"Техно", r"Филза", r"Ранбу",
]
UNIVERSE_CONTEXT = [
    r"L'Manberg", r"Ламанберг", r"Dream SMP", r"DSMP", r"сервер", r"Дрим СМП",
]
EXPLICIT_PAT = re.compile("|".join(EXPLICIT), re.IGNORECASE)
CHAR_PAT = re.compile("|".join(CHARACTERS), re.IGNORECASE)
CONTEXT_PAT = re.compile("|".join(UNIVERSE_CONTEXT), re.IGNORECASE)


def check(text):
    if not text:
        return False
    if EXPLICIT_PAT.search(text):
        return True
    char_matches = CHAR_PAT.findall(text)
    if len(char_matches) >= 2 and CONTEXT_PAT.search(text):
        return True
    return False
