# -*- coding: utf-8 -*-
"""Общие помощники для критериев тегов.

Имя с подчёркивания — загрузчик `fanfic_tags.load_criteria_modules`
такие файлы пропускает, так что модулем-критерием он не считается.

Главное здесь — граница начала слова. Без неё «раны» находились внутри
«страны» и «бараны», «ранен» внутри «странен»: тег ставился по словам,
не имеющим к теме отношения.

Граница ставится только слева. Справа нельзя: русский язык флективный,
и многие паттерны намеренно написаны как основа слова — «эктоплазм»
должен ловить «эктоплазмой», «Робин» — «Робином».
"""
from __future__ import annotations

import re

WORD_START = r"(?<!\w)"


def word_pattern(pattern: str) -> str:
    """Добавить границу начала слова."""
    return WORD_START + pattern


def compile_any(patterns: list[str], flags: int = re.IGNORECASE) -> re.Pattern:
    """Одна регулярка «любой из паттернов», у каждого своя граница."""
    return re.compile("|".join(word_pattern(p) for p in patterns), flags)


def search_any(patterns: list[str], text: str) -> bool:
    """Сработал хотя бы один паттерн."""
    return any(re.search(word_pattern(p), text, re.IGNORECASE) for p in patterns)


# Сколько букв должно совпасть, чтобы счесть паттерны формами одного слова.
# Пять — чтобы «довер|ие/ять/яет» склеились, а «Бэт|мен/пещера/семья» нет.
STEM_MIN = 5


def _same_marker(a: str, b: str) -> bool:
    """Два паттерна описывают один и тот же маркер?"""
    if a in b or b in a:
        return True
    common = 0
    for ca, cb in zip(a.lower(), b.lower()):
        if ca != cb:
            break
        common += 1
    # Считаем именно буквы: у «не верит» / «не верил» общее начало — «не вери»,
    # и пробел в нём не должен мешать признать их одним маркером.
    letters = sum(1 for c in a[:common] if c.isalpha())
    return letters >= STEM_MIN


def _groups(patterns: tuple[str, ...]) -> list[list[str]]:
    """Разбить паттерны на смысловые группы.

    Один маркер часто записан несколькими вариантами: вложенными
    («доверие» / «потерял доверие») или формами одного слова («доверие» /
    «доверять» / «доверяет»). Считать их разными нельзя — порог «2+ разных»
    тогда проходит одна фраза: «не доверяет» давало сразу два совпадения,
    «предал доверие» — три.
    """
    groups: list[list[str]] = []
    for pat in sorted(patterns, key=len):
        for g in groups:
            if any(_same_marker(pat, other) for other in g):
                g.append(pat)
                break
        else:
            groups.append([pat])
    return groups


_GROUP_CACHE: dict[tuple[str, ...], list[list[str]]] = {}


def group_patterns(patterns: list[str]) -> list[list[str]]:
    key = tuple(patterns)
    if key not in _GROUP_CACHE:
        _GROUP_CACHE[key] = _groups(key)
    return _GROUP_CACHE[key]


def count_occurrences(patterns: list[str], text: str) -> int:
    """Сколько раз паттерны встретились в тексте (все вхождения).

    Для тем, у которых маркер по сути один — «дракон» и его формы.
    Считать разные маркеры там нечего, а разовое упоминание в метафоре
    темой заметки не делает.
    """
    return sum(len(re.findall(word_pattern(p), text, re.IGNORECASE)) for p in patterns)


def count_distinct(patterns: list[str], text: str) -> int:
    """Сколько РАЗНЫХ смысловых маркеров сработало.

    Однокоренные варианты одного маркера засчитываются один раз.
    """
    return sum(1 for group in group_patterns(patterns) if search_any(group, text))


# Сколько слов слева от маркера смотреть на отрицание. Двух хватает:
# «это НЕ путешествие во времени», «магия НЕ машина времени».
NEG_WINDOW = 2
NEGATIONS = {"не", "ни"}
# «не просто X» и «не только X» — это утверждение X, а не отрицание.
NEG_EXCEPT = {"просто", "только", "столько"}
_WORD_RE = re.compile(r"\w+", re.UNICODE)


def is_negated(text: str, start: int) -> bool:
    """Маркер, начинающийся в позиции start, стоит под отрицанием?

    Тег ставит не слово, а утверждение. «Это не путешествие во времени» —
    прямое указание автора, что путешествия нет, и раньше оно давало тег
    наравне с настоящим сюжетом.
    """
    before = _WORD_RE.findall(text[max(0, start - 60) : start].lower())
    tail = before[-NEG_WINDOW:]
    if not tail or not (NEGATIONS & set(tail)):
        return False
    return tail[-1] not in NEG_EXCEPT


# Сколько символов после маркера смотреть на знак вопроса.
_Q_TAIL = 2


def is_guess(text: str, end: int) -> bool:
    """За маркером сразу знак вопроса — это перебор версий, а не сюжет.

    «— Клон? Магия? Путешествие во времени? Но ДНК...» — герой гадает вслух,
    и обычно тут же версию отбрасывает.
    """
    return "?" in text[end : end + _Q_TAIL]


def live_hits(patterns: list[str], text: str) -> int:
    """Сколько вхождений маркеров осталось после отсева отрицаний и догадок."""
    total = 0
    for pat in patterns:
        for m in re.finditer(word_pattern(pat), text, re.IGNORECASE):
            if is_negated(text, m.start()) or is_guess(text, m.end()):
                continue
            total += 1
    return total
