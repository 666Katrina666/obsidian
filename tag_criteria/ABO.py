# -*- coding: utf-8 -*-
"""#ABO - Alpha/Beta/Omega dynamics."""
import re

TAG = "ABO"

# Fully explicit — any single one is enough
EXPLICIT_PAT = re.compile(
    r"\bABO\b"
    r"|омега.?верс"          # омега-верс, омегаверс
    r"|omega.?verse"
    r"|альфа.?омега.?динамик" # "альфа-омега динамика" / "динамика альфа/омега"
    r"|динамик.{1,10}альфа.{1,20}омег" # "динамика альфы и омеги"
    r"|в мире альф.{1,10}омег"
    r"|мир альф и омег"
    r"|платонический або"
    r"|платонический ABO",
    re.IGNORECASE,
)

# Specific ABO terms — require 2+ different ones (not just generic «альфа»)
SPECIFIC = [
    r"течка",           # heat/rut — very ABO-specific
    r"запах омеги",
    r"запах альфы",
    r"запах беты",
    r"метка альфы",
    r"метка омеги",
    r"альфа пометил",
    r"пометить омег",
    r"вторичный пол",
    r"вторичные половые",
    r"альфа-зов",
    r"омега-зов",
]
SPECIFIC_PAT = [re.compile(p, re.IGNORECASE) for p in SPECIFIC]


def check(text):
    if not text:
        return False
    if EXPLICIT_PAT.search(text):
        return True
    # Require 2+ ABO-specific markers
    found = sum(1 for p in SPECIFIC_PAT if p.search(text))
    return found >= 2
