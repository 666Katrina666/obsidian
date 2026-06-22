# -*- coding: utf-8 -*-
"""#dc/bnha - DC + My Hero Academia crossover (both universes required).

'UA' removed as a standalone marker — too short, could be an abbreviation
for anything. Require at least one unambiguous MHA-specific marker alongside DC.
"""
import re

TAG = "dc/bnha"

DC_MARKERS_PAT = re.compile(
    r"Бэтсемья|Бэтпещера|Готэм|Бэтмен|Джейсон|Робин",
    re.IGNORECASE,
)

# Only unambiguous MHA markers — no bare 'UA'
BNHA_PAT = re.compile(
    r"\bMHA\b"
    r"|My Hero Academia"
    r"|Boku no Hero"
    r"|Боку но Хиро"
    r"|\bЮэй\b|\bЮей\b"            # UA school (RU name)
    r"|Олл Майт|All Might"
    r"|\bИзуку\b|\bМидория\b"
    r"|\bДеку\b"
    r"|геройская академия"
    r"|академия героев"
    r"|\bквирк"                      # quirk (RU)
    r"|\bquirk\b"                    # quirk (EN)
    r"|Бакуго|Бакугоу|Bakugo"
    r"|Тодороки|Todoroki"
    r"|Уравака|Uraraka"
    r"|Класс 1-А|Class 1-A",
    re.IGNORECASE,
)


def check(text):
    if not text:
        return False
    return bool(DC_MARKERS_PAT.search(text)) and bool(BNHA_PAT.search(text))
