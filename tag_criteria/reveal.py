# -*- coding: utf-8 -*-
"""#reveal - reveal, identity/secret reveal. Require 2+ markers."""
import re

TAG = "reveal"

PATTERNS = [
    r"раскрытие", r"раскрыл", r"раскрыла", r"раскрыл тайну",
    r"раскрытие личности", r"раскрытие идентичности", r"узнали кто он",
    r"узнали кто она", r"узнали правду", r"разоблачение", r"разоблачил",
    r"разоблачили", r"секрет раскрыт", r"тайна раскрыта", r"тайна выплыла",
    r"секрет открылся", r"маска снята", r"снял маску", r"сорвал маску",
    r"личность раскрыта", r"идентичность раскрыта", r"identity reveal",
    r"раскрытие тайны",
]


def check(text):
    if not text:
        return False
    found = set()
    for p in PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            found.add(p)
    return len(found) >= 2
