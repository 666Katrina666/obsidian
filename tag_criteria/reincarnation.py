# -*- coding: utf-8 -*-
"""#reincarnation - reincarnation."""
import re

TAG = "reincarnation"

PATTERNS = [
    r"реинкарнация", r"реинкарнировал", r"реинкарнировала", r"реинкарнат",
    r"перерождение", r"переродился", r"переродилась", r"переродиться",
    r"прошлая жизнь", r"прошлой жизни", r"память прошлой жизни",
    r"воспоминания прошлой жизни", r"прежняя жизнь", r"предыдущая жизнь",
    r"в новой жизни", r"новой жизни", r"в новом теле", r"новое тело",
    r"родился в новом теле", r"душа переродилась", r"душа перешла",
    r"родился заново", r"родилась заново", r"reincarnation",
]
PAT = re.compile("|".join(PATTERNS), re.IGNORECASE)


def check(text):
    return bool(text and PAT.search(text))
