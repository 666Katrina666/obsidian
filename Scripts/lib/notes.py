# -*- coding: utf-8 -*-
"""Разбор шапки заметки: строка тегов, описание, тело.

Единственный источник правды по формату шапки и по порядку тегов.
Раньше это жило в пяти скриптах с тремя разными регекспами и двумя
способами отрезать тело — расхождения давали разные теги на одних и тех
же файлах.

Формат заметки:

    #dc/dp #wings #reveal            <- строка тегов, первая, без префикса
                                     <- пустая
    Одно-два предложения описания.   <- описание, тоже без префикса
                                     <- пустая
    ---                              <- разделитель
    <тело>

Префиксы «Теги:» и «Описание:» из формата убраны, но чтение их всё ещё
понимает: заметки могли не пройти миграцию, да и руками их иногда пишут.

Над разделителем может стоять замок тегов — решение автора, которое сильнее
критерия:

    Одно-два предложения описания.
    %% tag-lock: -dc/marvel +dimentional_travel %%
    ---

«-тег» скрипты не ставят, даже если критерий срабатывает; «+тег» не снимают,
даже если критерий молчит. Это комментарий Obsidian: в режиме чтения строки
не видно, и «#» в ней нет, чтобы Obsidian не принял её за теги. Описанием
строка замка не считается.
"""
from __future__ import annotations

import re

# Порядок из «Иерархия_тегов.md», раздел «Порядок сортировки тегов в файлах».
TAG_ORDER = [
    # вселенные и кроссоверы
    "dc",
    "dc/dp",
    "dc/bnha",
    "dc/marvel",
    "dc/ori",
    "dc/undertale",
    "dc/concept/talon",
    "dc/concept/dark_Bruce",
    "dsmp",
    # сюжет
    "dimentional_travel",
    "time_travel",
    "time_loop",
    "reincarnation",
    "reveal",
    # трансформации
    "wings",
    "de-aging",
    "dragon",
    # магия
    "MahouShoujo",
    # прочее
    "ABO",
    # эмоции
]

_ORDER_INDEX = {tag: i for i, tag in enumerate(TAG_ORDER)}
_UNIVERSE_END = _ORDER_INDEX["dsmp"]
_MAGIC_INDEX = _ORDER_INDEX["MahouShoujo"]
_UNKNOWN_INDEX = len(TAG_ORDER)

TAG_PREFIX = "Теги: "
DESCRIPTION_PREFIX = "Описание: "
SEPARATOR = "---"

# Пустая шапка: строка тегов, пустая, описание, пустая, разделитель.
# Первая и третья строки пустые — их заполняют скриптом или руками.
HEADER_TEMPLATE = "\n\n\n\n" + SEPARATOR + "\n"

# Буквы, цифры, подчёркивание, дефис и слеш. Точка намеренно не входит:
# иначе «#dc.» съедало бы точку предложения в состав тега.
TAG_RE = re.compile(r"#([\w/-]+)")
_TAG_PREFIX_RE = re.compile(r"^\s*(?:Теги|Tags)\s*:\s*", re.IGNORECASE)
_DESCRIPTION_PREFIX_RE = re.compile(r"^\s*(?:Описание|Description)\s*:\s*", re.IGNORECASE)
# Разделитель шапки — «---» на отдельной строке. Не подходит «|---|---|»
# внутри markdown-таблицы: по нему тело резалось с потерей начала.
_SEPARATOR_RE = re.compile(r"---+\s*")
# Шапка — теги, пустая строка, описание, пустая строка, «---». Десять строк
# с запасом; дальше искать разделитель нельзя, там уже тело.
HEADER_MAX_LINES = 10
# Замок тегов: «%% tag-lock: -dc/marvel +dc %%» отдельной строкой в шапке.
_LOCK_RE = re.compile(r"\s*%%\s*tag-lock:\s*(.*?)\s*%%\s*")
_LOCK_ITEM_RE = re.compile(r"([+-])([\w/-]+)")


def strip_tag_prefix(line: str) -> str:
    """Снять необязательный префикс «Теги:» / «Tags:»."""
    return _TAG_PREFIX_RE.sub("", line.lstrip("﻿"), count=1)


def strip_description_prefix(line: str) -> str:
    """Снять необязательный префикс «Описание:» / «Description:»."""
    return _DESCRIPTION_PREFIX_RE.sub("", line.lstrip("﻿"), count=1)


def parse_tags(line: str) -> list[str]:
    """Теги из строки, без «#», без дубликатов, в исходном порядке."""
    if not line or not line.strip():
        return []
    return list(dict.fromkeys(TAG_RE.findall(strip_tag_prefix(line))))


def is_tag_line(line: str) -> bool:
    """Строка целиком состоит из тегов (префикс необязателен).

    Заголовок markdown («## Глава 1», «###») строкой тегов не считается.
    """
    if not line or not line.strip():
        return False
    rest = strip_tag_prefix(line).strip()
    if not rest:
        return False
    return all(TAG_RE.fullmatch(token) for token in rest.split())


def is_separator(line: str) -> bool:
    """Строка — разделитель шапки и тела: три и больше дефиса.

    Публичная обёртка над регекспом: сравнивать с литералом «---» нельзя,
    иначе строка с хвостовым пробелом или из четырёх дефисов перестаёт
    считаться разделителем, и вызывающий начинает расходиться с тем, как
    режет тело `body_after_separator`.
    """
    return bool(_SEPARATOR_RE.fullmatch(line))


def sort_tags(tags: list[str]) -> list[str]:
    """Упорядочить по иерархии. Неизвестные теги — в хвост, по алфавиту."""
    return sorted(tags, key=_tag_sort_key)


def _tag_sort_key(tag: str) -> tuple[int, str]:
    exact = _ORDER_INDEX.get(tag)
    if exact is not None:
        return (exact, "")
    if tag.startswith("dc/"):
        return (_UNIVERSE_END, tag)
    if tag.startswith("MahouShoujo/"):
        return (_MAGIC_INDEX, tag)
    return (_UNKNOWN_INDEX, tag)


def apply_dc_rule(tags: list[str]) -> list[str]:
    """«#dc» не ставится, если есть любой «#dc/*»."""
    if any(t.startswith("dc/") for t in tags):
        return [t for t in tags if t != "dc"]
    return tags


def normalize_tags(tags: list[str]) -> list[str]:
    """Убрать дубликаты, применить правило dc, упорядочить по иерархии."""
    return sort_tags(apply_dc_rule(list(dict.fromkeys(tags))))


def format_tag_line(tags: list[str]) -> str:
    """Собрать строку тегов в каноническом виде — без префикса."""
    return " ".join("#" + t for t in tags)


def split_note(text: str) -> tuple[str, str]:
    """Разбить на (первая строка, остальное). Перевод строки не теряется."""
    if "\n" not in text:
        return text, ""
    first, rest = text.split("\n", 1)
    return first, rest


def body_after_separator(text: str) -> str:
    """Тело заметки: всё после «---», закрывающего шапку.

    Разделитель ищется только в пределах шапки (первые HEADER_MAX_LINES
    строк) и только у заметок, где первая строка — строка тегов. Иначе
    горизонтальная линия в тексте или «|---|---|» из markdown-таблицы
    принимались за конец шапки, и начало тела терялось.
    """
    first, rest = split_note(text)
    if not has_tag_header(text):
        return text

    head_lines = rest.split("\n")[:HEADER_MAX_LINES]
    offset = 0
    for line in head_lines:
        if is_separator(line):
            return rest[offset + len(line) :].lstrip("\n")
        offset += len(line) + 1
    return rest


def has_tag_header(text: str) -> bool:
    """У заметки есть шапка, даже если тегов в ней нет.

    Три случая: строка тегов; старая «Теги: » с пустым списком; пустая
    первая строка, за которой в пределах шапки идёт «---» (так выглядит
    заметка без тегов после миграции).
    """
    first, rest = split_note(text)
    stripped = first.lstrip("﻿").strip()
    if _TAG_PREFIX_RE.match(stripped):
        return True
    if is_tag_line(first):
        return True
    if stripped:
        return False
    head = rest.split("\n")[:HEADER_MAX_LINES]
    return any(is_separator(line) for line in head)


def set_tag_line(text: str, tag_line: str) -> str:
    """Заменить строку тегов, а если шапки нет — вставить её перед телом.

    Без этой развилки заметка без шапки теряла первую строку: код просто
    писал теги на её место. В Beta первая строка — «**Вы:**», по которой
    конвейер находит исходный промпт.
    """
    if has_tag_header(text):
        _first, rest = split_note(text)
        return tag_line + "\n" + rest
    return tag_line + "\n\n" + text


def tags_of(text: str) -> list[str]:
    """Теги заметки, если первая строка — строка тегов."""
    first, _rest = split_note(text)
    return parse_tags(first) if is_tag_line(first) else []


def header_lines(text: str) -> list[str]:
    """Строки шапки между строкой тегов и «---». Без шапки — пусто."""
    if not has_tag_header(text):
        return []
    _first, rest = split_note(text)
    out = []
    for line in rest.split("\n")[:HEADER_MAX_LINES]:
        if is_separator(line):
            return out
        out.append(line)
    return []


def is_lock_line(line: str) -> bool:
    """Строка — замок тегов."""
    return bool(_LOCK_RE.fullmatch(line))


def description_lines(text: str) -> list[str]:
    """Непустые строки описания: шапка без пустых строк и без замка."""
    return [l for l in header_lines(text) if l.strip() and not is_lock_line(l)]


def tag_lock(text: str) -> tuple[set[str], set[str]]:
    """Замок заметки: (что не ставить, что не снимать)."""
    forbid: set[str] = set()
    keep: set[str] = set()
    for line in header_lines(text):
        m = _LOCK_RE.fullmatch(line)
        if not m:
            continue
        for sign, tag in _LOCK_ITEM_RE.findall(m.group(1)):
            (keep if sign == "+" else forbid).add(tag)
    return forbid, keep


def apply_tag_lock(tags: list[str], lock: tuple[set[str], set[str]]) -> list[str]:
    """Поправить вычисленные теги по замку и нормализовать."""
    forbid, keep = lock
    return normalize_tags([t for t in tags if t not in forbid] + sorted(keep))


def format_lock_line(forbid: set[str], keep: set[str]) -> str:
    items = [f"-{t}" for t in sort_tags(list(forbid))] + [f"+{t}" for t in sort_tags(list(keep))]
    return f"%% tag-lock: {' '.join(items)} %%"


def set_tag_lock(text: str, forbid: set[str], keep: set[str]) -> str:
    """Записать замок строкой над «---»; прежний замок заменяется целиком.

    Заметка без шапки или без разделителя в пределах шапки не трогается:
    куда ставить замок, там не определить.
    """
    if not has_tag_header(text):
        return text
    first, rest = split_note(text)
    lines = rest.split("\n")
    sep = next((i for i, l in enumerate(lines[:HEADER_MAX_LINES]) if is_separator(l)), None)
    if sep is None:
        return text
    head = [l for l in lines[:sep] if not is_lock_line(l)]
    while head and not head[-1].strip():
        head.pop()
    if not head:
        head = [""]
    if forbid or keep:
        head.append(format_lock_line(forbid, keep))
    head.append("")
    return first + "\n" + "\n".join(head + lines[sep:])
