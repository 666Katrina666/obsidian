# -*- coding: utf-8 -*-
"""Разбор диалога внутри тела заметки: где запрос, где ответ, где размышления.

Модуль-близнец `notes.py`: там шапка, здесь тело. Свой способ найти запрос
заводить нельзя — иначе конвертер, выжимка описаний и поиск перезапусков
разойдутся в границах прогона и начнут спорить о том, чего в файле нет.

Форматов два, читаются оба:

- **старый** — служебные строки `**Вы:**` и `**Ассистент:**` посреди прозы;
- **новый** — запрос в свёрнутом callout `> [!question]- Запрос N`, ответ идёт
  дальше обычной прозой без всякого маркера. Блок размышлений модели, если он
  сохранился в дампе, лежит в отдельном `> [!abstract]- Размышления`.

Переходный период нужен по-настоящему: конвертация идёт папками, и между
`Beta` и `Fanfics` хранилище какое-то время живёт в обоих форматах сразу.
"""
from __future__ import annotations

import re

PROMPT_LABEL = "Запрос"
THINK_LABEL = "Размышления"
PROMPT_CALLOUT = "question"
THINK_CALLOUT = "abstract"

OLD_PROMPT_MARK = "**Вы:**"
OLD_ANSWER_MARK = "**Ассистент:**"
# Второй вид дампа (188 черновиков Beta): запрос идёт голым абзацем, а границу
# ответа показывает строка вида «Думал на протяжении 11s» — артефакт интерфейса,
# самих размышлений в ней нет.
THINKING_MARK_RE = re.compile(r"^\s*Думал на протяжении\b")

_CALLOUT_RE = re.compile(r"^\s*>\s*\[!(\w+)\][-+]?\s*(.*)$")
_QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
# Заголовок главы внутри ответа: по нему в выжимке видно, что прогон породил.
HEAD_RE = re.compile(r"^(#{1,4}\s|\*\*Глава)")


class Run:
    """Один прогон: запрос и то, что он породил.

    `start` — строка, с которой прогон начинается (маркер или callout),
    `end` — начало следующего прогона. Границы намеренно такие же, как были
    у старого разбора: по ним `rerolls.py` вырезает отвергнутые прогоны.
    """

    __slots__ = ("start", "end", "prompt", "head", "size", "think", "answer_start")

    def __init__(self, start: int, end: int, prompt: str, head: str, size: int,
                 think: str = "", answer_start: int | None = None):
        self.start, self.end = start, end
        self.prompt, self.head, self.size = prompt, head, size
        self.think = think
        self.answer_start = answer_start


def is_prompt_start(line: str) -> bool:
    """Строка открывает запрос — в любом из двух форматов."""
    if line.strip() == OLD_PROMPT_MARK:
        return True
    m = _CALLOUT_RE.match(line)
    return bool(m and m.group(1).lower() == PROMPT_CALLOUT)


def uses_new_format(lines: list[str]) -> bool:
    return any(_is_callout(l, PROMPT_CALLOUT) for l in lines)


def uses_thinking_format(lines: list[str]) -> bool:
    """Дамп второго вида: границу показывает строка «Думал на протяжении…»."""
    return any(THINKING_MARK_RE.match(l) for l in lines)


def is_spacer(line: str) -> bool:
    """Строка из одних пробелов — разделитель абзацев в дампе второго вида.

    От пустой отличается тем, что в ней есть пробелы; именно она отбивает
    запрос от прозы. Обычная пустая строка такой роли не несёт, и путать их
    нельзя: цикл «пропустить пустое» проскакивает разделитель насквозь.
    """
    return not line.strip() and line != ""


def _is_callout(line: str, kind: str) -> bool:
    m = _CALLOUT_RE.match(line)
    return bool(m and m.group(1).lower() == kind)


def _quote_body(lines: list[str], start: int, end: int) -> tuple[list[str], int]:
    """Строки callout начиная со `start` (заголовок уже прочитан) и где он кончился."""
    out: list[str] = []
    j = start
    while j < end:
        m = _QUOTE_RE.match(lines[j])
        if m is None:
            break
        if m.group(1).strip():
            out.append(m.group(1).strip())
        j += 1
    return out, j


def _find_head(lines: list[str], start: int, stop: int) -> str:
    """Первый заголовок главы в окне [start, stop). Окно узкое намеренно:
    заголовок ищется в начале ответа, а не где-нибудь в середине главы."""
    for k in range(start, stop):
        s = lines[k].strip()
        if HEAD_RE.match(s):
            return s
    return ""


def _parse_new(lines: list[str]) -> list[Run]:
    starts = [i for i, l in enumerate(lines) if _is_callout(l, PROMPT_CALLOUT)]
    runs = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        first = _CALLOUT_RE.match(lines[i]).group(2).strip()
        prompt, j = _quote_body(lines, i + 1, end)
        if first and not first.startswith(PROMPT_LABEL):
            # Заголовок callout несёт текст, а не подпись «Запрос N» — не терять.
            prompt.insert(0, first)

        think: list[str] = []
        k = j
        while k < end and not lines[k].strip():
            k += 1
        if k < end and _is_callout(lines[k], THINK_CALLOUT):
            think, k = _quote_body(lines, k + 1, end)
            j = k

        size = sum(1 for l in lines[j:end] if l.strip())
        runs.append(Run(i, end, " ".join(prompt), _find_head(lines, j, min(j + 7, end)),
                        size, " ".join(think), j))
    return runs


def _parse_old(lines: list[str]) -> list[Run]:
    starts = [i for i, l in enumerate(lines) if l.strip() == OLD_PROMPT_MARK]
    runs = []
    for n, i in enumerate(starts):
        end = starts[n + 1] if n + 1 < len(starts) else len(lines)
        j, prompt = i + 1, []
        while j < end and lines[j].strip() != OLD_ANSWER_MARK:
            if lines[j].strip():
                prompt.append(lines[j].strip())
            j += 1
        size = sum(1 for l in lines[j + 1:end] if l.strip())
        runs.append(Run(i, end, " ".join(prompt),
                        _find_head(lines, j + 1, min(j + 8, end)), size,
                        "", min(j + 1, end)))
    return runs


def parse_runs(lines: list[str]) -> list[Run]:
    """Прогоны тела заметки. Формат определяется по самому телу."""
    return _parse_new(lines) if uses_new_format(lines) else _parse_old(lines)


# Чем начинается запрос, если разделителя над ним нет. Список намеренно
# из глаголов-команд и слов, которыми автор начинает запрос; проза так
# начинается редко, а решает он лишь спорные случаи.
_COMMAND_RE = re.compile(
    r"^\s*(напиши|распиши|продолжи|помоги|давай|сделай|добавь|перепиши|следующ"
    r"|ещё|еще|теперь|длинная\s+глава|глава\b|альтернатив|идея|хочу|можешь"
    r"|а\s+теперь)", re.IGNORECASE)

# Больше этого числа строк подряд без разделителя — уже не запрос, а проза.
_MAX_LOOSE_PROMPT = 8


def _leading_prompt(lines: list[str], mark: int) -> int | None:
    """Индекс запроса, стоящего в самом верху тела, — или None.

    Обычно перед первой служебной строкой лежит только запрос. Но в части
    черновиков там **две** вещи: запрос сверху и уже начало ответа под ним
    (модель сперва отвечает одной фразой, потом идёт «Думал…» и полный текст).
    Тогда запрос — верхняя строка, а не та, что примыкает к маркеру.

    Признак: до примыкающего блока есть ещё непустой текст. Проверено на всём
    хранилище — так устроены ровно четыре черновика.
    """
    body = [i for i in range(mark) if lines[i].strip()]
    if len(body) < 2:
        return None
    j = mark - 1
    while j >= 0 and not lines[j].strip():
        j -= 1
    k = j
    while k >= 0 and not is_spacer(lines[k]):
        k -= 1
    above = [i for i in range(max(k, 0)) if lines[i].strip()]
    return above[0] if above else None


class Segment:
    """Кусок дампа второго вида: запрос (если он есть) и что за ним.

    `kind` говорит, откуда взялась граница запроса: `spacer` — отбит
    разделителем, `short` — разделителя нет, но блок короткий, `command` —
    опознан по первому слову, `none` — запроса нет вовсе, генерацию
    продолжили без текста.
    """

    __slots__ = ("kind", "prompt_start", "prompt_end", "mark", "end")

    def __init__(self, kind: str, prompt_start: int, prompt_end: int,
                 mark: int, end: int):
        self.kind = kind
        self.prompt_start, self.prompt_end = prompt_start, prompt_end
        self.mark, self.end = mark, end


def thinking_segments(lines: list[str]) -> list[Segment]:
    """Границы запросов в дампе второго вида.

    Запрос лежит перед строкой «Думал на протяжении…», но своего маркера
    не имеет, поэтому начало ищется назад: до разделителя из пробелов,
    а если его нет — по длине блока и по первому слову.
    """
    marks = [i for i, l in enumerate(lines) if THINKING_MARK_RE.match(l)]
    out: list[Segment] = []
    for n, mark in enumerate(marks):
        if n == 0:
            lead = _leading_prompt(lines, mark)
            if lead is not None:
                end = marks[1] if len(marks) > 1 else len(lines)
                out.append(Segment("leading", lead, lead + 1, mark, end))
                continue
        floor = marks[n - 1] if n else -1
        end = marks[n + 1] if n + 1 < len(marks) else len(lines)

        j = mark - 1
        while j > floor and not lines[j].strip():
            j -= 1
        if j <= floor:
            out.append(Segment("none", mark, mark, mark, end))
            continue

        k, count, spaced = j, 0, False
        while k > floor:
            if is_spacer(lines[k]):
                spaced = True
                break
            if lines[k].strip():
                count += 1
            k -= 1

        if spaced:
            kind, start = "spacer", k + 1
        elif count <= _MAX_LOOSE_PROMPT:
            kind, start = "short", k + 1
        elif _COMMAND_RE.match(lines[j]):
            kind, start = "command", j
        else:
            out.append(Segment("none", mark, mark, mark, end))
            continue

        while start < j and not lines[start].strip():
            start += 1
        out.append(Segment(kind, start, j + 1, mark, end))
    return out


def render_callout(kind: str, title: str, lines: list[str]) -> list[str]:
    """Собрать callout. Пишущие тоже ходят сюда, а не клеят строки сами.

    Пустая строка внутри становится `>`: без этого callout обрывается на
    первом же пропуске и хвост запроса вываливается в прозу отдельным абзацем.
    """
    body = list(lines)
    while body and not body[0].strip():
        body.pop(0)
    while body and not body[-1].strip():
        body.pop()
    head = f"> [!{kind}]- {title}".rstrip()
    return [head] + [f"> {l.rstrip()}" if l.strip() else ">" for l in body]
