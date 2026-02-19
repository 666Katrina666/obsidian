# -*- coding: utf-8 -*-
"""#reincarnation - reincarnation. No generic 'new life/body' alone."""
import re

TAG = "reincarnation"

# Explicit reincarnation markers. Forbidden as sole criterion: в новой жизни, новое тело, etc.
PATTERNS = [
    r"реинкарнация", r"реинкарнировал", r"реинкарнировала", r"реинкарнат",
    r"перерождение", r"переродился", r"переродилась", r"переродиться",
    r"прошлая жизнь", r"прошлой жизни", r"память прошлой жизни",
    r"воспоминания прошлой жизни", r"прежняя жизнь", r"предыдущая жизнь",
    r"родился в новом теле", r"душа переродилась", r"душа перешла",
    r"родился заново", r"родилась заново", r"reincarnation",
]
PAT = re.compile("|".join(PATTERNS), re.IGNORECASE)


def check(text):
    if not text:
        return False
    found = set()
    for p in PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            found.add(p)
    return len(found) >= 2
