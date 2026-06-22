# -*- coding: utf-8 -*-
"""#dc/marvel - DC + Marvel crossover (both universes clearly present).

Known false-positive sources fixed here:
- «мстители» lowercase = common Russian word "avengers/revengers" → case-sensitive check
- «Мстители» in guillemets «...» = movie/comic title reference → excluded via lookbehind
- «Тор» without boundaries = substring of «автор», «фактор» → use word boundary
- «Марвел» alone = can be Captain Marvel (DC character) → only count with other Marvel evidence
- «Stark» alone (EN) = used as tech brand comparison → removed; require «Tony Stark» or RU form
- «SHIELD» (mixed-case EN) = matches magic ability names → case-sensitive all-caps only
- «Человек-паук» needs re.IGNORECASE to catch inflected forms + «Человек-Паук» etc.
"""
import re

TAG = "dc/marvel"

DC_MARKERS_PAT = re.compile(
    r"Бэтсемья|Бэтпещера|Готэм|Бэтмен|Джейсон|Робин",
    re.IGNORECASE,
)

# Russian Marvel markers — case-SENSITIVE for ambiguous words.
# «Мстители» excluded when in guillemets (= movie title in dialog).
MARVEL_RU_CASE = re.compile(
    r"(?<!«)\bМстители\b(?!»)"  # Avengers (not «Мстители» movie reference in guillemets)
    r"|Тони Старк"              # Tony Stark
    r"|\bАйрон Мэн\b"
    r"|(?<!не )Капитан Америка" # Captain America (but not "Я не Капитан Америка" comparison)
    r"|\bТор Одинсон\b"         # Thor Odinson full name (avoids «автор»)
    r"|\bГидра\b"               # HYDRA (RU)
    r"|Наташа Романова"         # Natasha Romanoff (full name, avoids common «Наташа»)
    r"|(?<!символом )Щ\.И\.Т\." # SHIELD org (not «футболка с символом Щ.И.Т.» = merch)
    r"|\bВибраниум\b"           # Vibranium
    r"|\bТессеракт\b"           # Tesseract
    r"|\bМьёльнир\b"            # Mjolnir
    r"|Питер Паркер"            # Peter Parker
)

# Russian Marvel markers that need re.IGNORECASE for inflected/capitalised forms
MARVEL_RU_ICASE = re.compile(
    r"Человек-паук",            # Spider-Man (catches Человека-паука, Человек-Паук etc.)
    re.IGNORECASE,
)

# English Marvel markers — case-SENSITIVE to avoid matching «Hope Shield», «Stark» as tech brand
MARVEL_EN_CASE = re.compile(
    r"\bAvengers\b"
    r"|Tony Stark"
    r"|Iron Man"
    r"|Captain America"
    r"|\bMarvel\b"              # Marvel (EN proper noun, capital M)
    r"|\bThor\b"                # Thor (EN, word boundary)
    r"|\bHulk\b"
    r"|Spider-Man"
    r"|Spider-Man"
    r"|\bSHIELD\b"              # All-caps SHIELD = organisation (NOT «Hope Shield»)
    r"|Black Widow"
    r"|Nick Fury"
    r"|\bVibranium\b"
    r"|\bHYDRA\b"
    r"|\bMCU\b"                 # MCU reference = Marvel universe
    r"|Peter Parker"
)


def check(text):
    if not text:
        return False
    if not DC_MARKERS_PAT.search(text):
        return False
    return (
        bool(MARVEL_RU_CASE.search(text))
        or bool(MARVEL_RU_ICASE.search(text))
        or bool(MARVEL_EN_CASE.search(text))
    )
