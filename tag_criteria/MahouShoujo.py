# -*- coding: utf-8 -*-
"""#MahouShoujo - magical girl/boy genre or explicit franchises. No generic words."""
import re

TAG = "MahouShoujo"

# Only specific mahou shoujo / franchise markers. No: преображение, контракт, питомец, медальон, кристалл.
PATTERNS = [
    r"магическая девочка", r"магический мальчик", r"махо-сёдзё", r"mahou shoujo",
    r"magical girl", r"Sailor Moon", r"Сейлор Мун", r"Pretty Cure", r"Прети Кюр",
    r"Прекрасная Кюр", r"Tokyo Mew Mew", r"Токио Мяу Мяу", r"Tokyo Mew",
    r"W\.I\.T\.C\.H", r"В\.И\.Т\.Ч", r"Cure\s", r"Кардкоптор", r"Cardcaptor",
    r"в магическую форму", r"превращается в магического воина", r"магические карты",
    r"медальон.*магическ|магическ.*медальон",
]


def check(text):
    if not text:
        return False
    found = set()
    for p in PATTERNS:
        if re.search(p, text, re.IGNORECASE):
            found.add(p)
    return len(found) >= 2
