# -*- coding: utf-8 -*-
"""#MahouShoujo - magical girl/boy genre."""
import re

TAG = "MahouShoujo"

PATTERNS = [
    r"магическая девочка", r"магический мальчик", r"махо-сёдзё", r"mahou shoujo",
    r"magical girl", r"Sailor", r"Sailor Moon", r"Сейлор Мун", r"Cure",
    r"Pretty Cure", r"Прети Кюр", r"Прекрасная Кюр", r"Tokyo Mew", r"Токио Мяу",
    r"Токио Мяу Мяу", r"W\.I\.T\.C\.H", r"В\.И\.Т\.Ч", r"преображение",
    r"в магическую форму", r"превращается в магического воина", r"магические карты",
    r"контракт", r"питомец", r"медальон", r"кристалл",
]
PAT = re.compile("|".join(PATTERNS), re.IGNORECASE)


def check(text):
    return bool(text and PAT.search(text))
