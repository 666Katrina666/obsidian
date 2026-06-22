# -*- coding: utf-8 -*-
"""#dsmp - Dream SMP universe.

Only set when text is clearly set IN the DSMP universe.
False-positive fixed: removed «сервер» from context — it's a common Russian word
(Batcave servers, computer servers) that paired with generic names like «Томми»
was causing 140+ false matches. Now requires explicit DSMP universe markers only.
"""
import re

TAG = "dsmp"

# Only explicit, unambiguous DSMP universe references
EXPLICIT = [
    r"Dream SMP",
    r"Дрим СМП",
    r"ДримСМП",
    r"\bDSMP\b",
    r"L'Manberg",
    r"Л'Манберг",
    r"Ламанберг",
    r"Л-Манберг",
]
EXPLICIT_PAT = re.compile("|".join(EXPLICIT), re.IGNORECASE)

# Character names are NOT sufficient alone — too common in DC fic context.
# They only help if paired with a strict explicit DSMP universe marker.
CHARACTERS = [
    r"\bТехноблэйд\b", r"\bTechnoblade\b",
    r"\bФилза\b", r"\bPhilza\b",
    r"\bТуббо\b", r"\bTubbo\b",
    r"\bСапНап\b", r"\bSapNap\b",
    r"\bЛ'Манберг\b",
]
CHAR_PAT = re.compile("|".join(CHARACTERS), re.IGNORECASE)


def check(text):
    if not text:
        return False
    # Require at least one fully explicit DSMP marker
    if EXPLICIT_PAT.search(text):
        return True
    # OR: very specific DSMP character name (not just "Томми"/"Вилбур") + explicit marker
    if CHAR_PAT.search(text) and EXPLICIT_PAT.search(text):
        return True
    return False
