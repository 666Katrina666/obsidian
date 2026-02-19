# -*- coding: utf-8 -*-
"""#dimentional_travel - dimensional travel, alternate worlds. Require 2+ markers."""
import re

TAG = "dimentional_travel"

PATTERNS = [
    r"другой мир", r"иной мир", r"другая вселенная", r"иная вселенная",
    r"альтернативн", r"параллельн", r"портал", r"измерение", r"измерения",
    r"между измерениями", r"мультивселенная", r"мультиверс",
    r"попал в мир", r"попала в мир", r"попали в мир", r"перешел в мир",
    r"оказался в другом мире", r"занесло в другой мир", r"между мирами",
    r"из другого мира", r"в другом мире", r"попаданц", r"dimensional travel",
    r"путешествие между мирами",
]


def check(text):
    if not text:
        return False
    found = set()
    for p in PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            found.add(p)
    return len(found) >= 2
