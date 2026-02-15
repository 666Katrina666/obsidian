# -*- coding: utf-8 -*-
"""#dimentional_travel - dimensional travel, alternate worlds."""
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
PAT = re.compile("|".join(PATTERNS), re.IGNORECASE)


def check(text):
    return bool(text and PAT.search(text))
