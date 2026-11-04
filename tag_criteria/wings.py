# -*- coding: utf-8 -*-
"""#wings - wings and flight (not just birds)."""
import re

import _common

TAG = "wings"

WING_WORDS = [
    r"крылья", r"крылатый", r"крыльев", r"перья", r"перьев", r"оперение",
]
WING_PAT = _common.compile_any(WING_WORDS)

CONTEXT_MARKERS = [
    r"Джейсон", r"Бэтсемья", r"Готэм", r"трансформация", r"магическ", r"форма",
]
CONTEXT_PAT = _common.compile_any(CONTEXT_MARKERS)

BIRD_ONLY = re.compile(r"птицы|орнитолог|перелётные", re.IGNORECASE)


def check(text):
    if not text:
        return False
    wing_matches = len(WING_PAT.findall(text))
    if wing_matches < 3:
        return False
    if BIRD_ONLY.search(text) and not CONTEXT_PAT.search(text):
        return False
    return True
