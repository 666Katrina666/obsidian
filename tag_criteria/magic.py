# -*- coding: utf-8 -*-
"""#magic - magic (require 2+ different markers)."""
import re

TAG = "magic"

PATTERNS = [
    r"магия", r"магическ", r"заклинание", r"заклинания", r"заклинаний",
    r"прочитал заклинание", r"ритуал", r"ритуалы", r"ритуальный",
    r"артефакт", r"магический артефакт", r"колдовство", r"колдун", r"колдунья",
    r"волшебств", r"чары", r"зачарован", r"проклятие", r"проклял", r"снять проклятие",
    r"магическая энергия", r"магическая сила", r"некромантия", r"некромант",
    r"маг", r"волшебник", r"spell", r"magic",
]


def check(text):
    if not text:
        return False
    found = set()
    for pat in PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            found.add(pat)
    return len(found) >= 2
