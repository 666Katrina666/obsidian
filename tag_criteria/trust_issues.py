# -*- coding: utf-8 -*-
"""#trust_issues - trust issues (2+ markers)."""
import re

TAG = "trust_issues"

PATTERNS = [
    r"доверие", r"доверять", r"доверяет", r"не доверяет", r"потерял доверие",
    r"потеря доверия", r"вернуть доверие", r"заслужить доверие", r"нарушил доверие",
    r"проблемы с доверием", r"с доверием проблемы", r"предательство", r"предал",
    r"предали", r"предать", r"предал доверие", r"обман", r"обманул", r"обманули",
    r"обманывал", r"не верит", r"не верил", r"не верит ему", r"сомневается",
    r"сомнение", r"сомневался", r"подозревает", r"подозрение", r"подозревал",
    r"trust issues",
]


def check(text):
    if not text:
        return False
    found = sum(1 for p in PATTERNS if re.search(p, text, re.IGNORECASE))
    return found >= 2
