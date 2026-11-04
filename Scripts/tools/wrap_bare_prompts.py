# -*- coding: utf-8 -*-
"""Оборачивает голые запросы в callout по карте границ, составленной вручную.

У части заметок `Fanfics` нет никакой разметки диалога: ни `**Вы:**`, ни
строки «Думал на протяжении…», часто даже пустой строки между запросом и
ответом. Граница там видна только по смыслу, поэтому её не ищут регекспом,
а читают глазами и записывают в карту `Notes/prompt_map.json`:

    {
      "240. Jason and Steph's Underground Journey.md": {
        "prompts": [[6, 8, "напиши длинную"]]
      },
      "58. Accidental 'Dad' - The Slip That Binds.md": {
        "lost": [[6, "Этот концепт"], [209, "# Глава: Случайное слово"]]
      }
    }

- `prompts` — диапазоны строк запроса: номера строк **файла**, с единицы,
  оба конца включительно. Третье поле — начало первой строки запроса:
  если файл сдвинулся с момента разметки, скрипт его не тронет.
- `lost` — ответы, запрос к которым не сохранился: `[строка, якорь]` —
  первая строка такого ответа. Перед ней встаёт callout-заглушка с текстом
  `LOST_PROMPT`: по нему такие места найдутся, когда дойдёт черёд
  восстанавливать запросы. `lost: true` — то же для начала тела.
  Сочетается с `prompts` в одной заметке.
- `review` — причина вернуться к заметке позже: границы ответов не видны
  (одна заглушка на всю заметку) или поставлены наугад. Скрипт её не
  читает при обёртке, а только собирает список в конец отчёта — по всей
  карте, включая заметки, обёрнутые прошлыми партиями.

Каждый собранный файл проверяется той же сверкой, что у
`convert_prompt_markup.py`: весь значимый текст обязан совпасть по порядку,
разрешено только приписать `> ` строкам запроса и добавить заглушку. Плюс
`parse_runs` нового тела обязан найти ровно столько прогонов, сколько
запросов в карте, с тем же текстом.

Отчёт с каждой границей — запрос и первые строки ответа под ним —
пишется в `Reports/wrap_bare_prompts_report.md`, по нему границы и сверяют.

По умолчанию ничего не меняет. Запись — с `--apply`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
import notes
import runs as runs_mod
from paths import notes_dir, reports_dir, vault_root
from convert_prompt_markup import content_seq

VAULT = vault_root(__file__)
MAP_FILE = notes_dir(__file__) / "prompt_map.json"
REPORT_FILE = "wrap_bare_prompts_report.md"

# Текст заглушки. Менять нельзя без прогона по хранилищу: по нему
# будущий шаг найдёт заметки, у которых запрос надо восстановить.
LOST_PROMPT = "(запрос не сохранился)"


class MapError(Exception):
    pass


def body_offset(text: str) -> tuple[int, list[str]]:
    """Номер строки файла (с нуля), с которой начинается тело, и само тело."""
    body_text = notes.body_after_separator(text)
    prefix = text[:len(text) - len(body_text)] if body_text else text
    return prefix.count("\n"), body_text.split("\n")


def trim(lines: list[str]) -> list[str]:
    out = list(lines)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def wrap(body: list[str], spans: list[tuple[int, int]]) -> list[str]:
    """Новое тело. `spans` — индексы строк тела, конец не включён.

    Пустой отрезок (`start == end`) — место, где ответ идёт без запроса:
    туда встаёт заглушка, а сам текст не трогается.
    """
    out: list[str] = []
    cursor = 0
    for n, (start, end) in enumerate(spans, start=1):
        # Хвост прошлого ответа (или преамбула перед первым запросом) — как есть.
        before = trim(body[cursor:start])
        if before:
            out.extend(before)
            out.append("")
        prompt = body[start:end] if end > start else [LOST_PROMPT]
        out.extend(runs_mod.render_callout(runs_mod.PROMPT_CALLOUT,
                                           f"{runs_mod.PROMPT_LABEL} {n}", prompt))
        out.append("")
        cursor = end
    out.extend(trim(body[cursor:]))
    return out


def prompt_text(body: list[str], start: int, end: int) -> str:
    if end == start:
        return LOST_PROMPT
    return " ".join(l.strip() for l in body[start:end] if l.strip())


def check(body: list[str], new_body: list[str], spans: list[tuple[int, int]]) -> str:
    """Пустая строка — всё сошлось, иначе причина отказа."""
    old = content_seq(body, new_format=False)
    new = [s for s in content_seq(new_body, new_format=True) if s != LOST_PROMPT]
    if old != new:
        if len(old) != len(new):
            return f"строк текста было {len(old)}, стало {len(new)}"
        for k, (a, b) in enumerate(zip(old, new), start=1):
            if a != b:
                return f"строка {k} разошлась: {a[:40]!r} против {b[:40]!r}"
        return "неизвестное расхождение"

    parsed = runs_mod.parse_runs(new_body)
    expected = [prompt_text(body, s, e) for s, e in spans]
    got = [r.prompt for r in parsed]
    if len(got) != len(expected):
        return f"parse_runs нашёл {len(got)} прогонов, в карте {len(expected)}"
    for k, (a, b) in enumerate(zip(expected, got), start=1):
        # parse_runs снимает только один уровень цитаты, как и сверка выше.
        if a.replace("> ", "").replace(">", "") != b.replace("> ", "").replace(">", ""):
            return f"запрос {k} прочитан иначе: {b[:50]!r}"
    return ""


def _line(file_lines: list[str], offset: int, line: int, anchor: str) -> int:
    """Номер строки файла → индекс тела, с проверкой якоря."""
    if not (1 <= line <= len(file_lines)):
        raise MapError(f"строка {line} вне файла ({len(file_lines)} строк)")
    if line - 1 < offset:
        raise MapError(f"строка {line} лежит в шапке")
    if not file_lines[line - 1].strip().startswith(anchor):
        raise MapError(f"строка {line} не начинается с {anchor!r}: "
                       f"{file_lines[line - 1].strip()[:50]!r}")
    return line - 1 - offset


def resolve(entry: dict, text: str) -> list[tuple[int, int]]:
    """Перевести карту в отрезки тела и проверить якоря.

    `lost: true` — заглушка в начале тела; `lost: [[строка, якорь], …]` —
    заглушки перед ответами, у которых запрос пропал посреди заметки.
    """
    offset, body = body_offset(text)
    file_lines = text.split("\n")
    spans: list[tuple[int, int]] = []
    for item in entry.get("prompts", []):
        if len(item) != 3:
            raise MapError(f"диапазон {item}: нужно [начало, конец, якорь]")
        start, end, anchor = item
        if end < start:
            raise MapError(f"диапазон {start}-{end} перевёрнут")
        spans.append((_line(file_lines, offset, start, anchor), end - offset))
    lost = entry.get("lost", [])
    if lost is True:
        first = next((i for i, l in enumerate(body) if l.strip()), 0)
        spans.append((first, first))
    else:
        for item in lost:
            if len(item) != 2:
                raise MapError(f"заглушка {item}: нужно [строка, якорь]")
            k = _line(file_lines, offset, *item)
            spans.append((k, k))
    if not spans:
        raise MapError("ни запросов, ни заглушек")
    spans.sort()
    for (a0, a1), (b0, b1) in zip(spans, spans[1:]):
        if b0 < a1 or (a0, a1) == (b0, b1):
            raise MapError("отрезки перекрываются")
    for a, b in zip(spans, spans[1:]):
        if not trim(body[a[1]:b[0]]):
            raise MapError(f"между запросами у строки {a[1] + offset} нет ответа")
    return spans


def describe(body: list[str], spans: list[tuple[int, int]], offset: int) -> list[str]:
    """Строки отчёта: каждый запрос и начало ответа под ним."""
    out: list[str] = []

    def answer_head(pos: int) -> str:
        heads = [l.strip() for l in body[pos:pos + 40] if l.strip()][:2]
        return " / ".join(h[:110] for h in heads)

    for n, (start, end) in enumerate(spans, start=1):
        if start == end:
            out.append(f"- **Запрос {n}** — заглушка (строка {start + offset + 1})")
        else:
            prompt = prompt_text(body, start, end)
            short = prompt if len(prompt) <= 300 else prompt[:300] + "…"
            out.append(f"- **Запрос {n}** (строки {start + offset + 1}–{end + offset}): {short}")
        out.append(f"  - ответ: {answer_head(end)}")
    return out


def review_list(directory: Path, mapping: dict) -> list[tuple[str, int, str]]:
    """Заметки с пометкой `review`, от длинных к коротким: длинные важнее."""
    out = []
    for name, entry in mapping.items():
        if not entry.get("review"):
            continue
        path = directory / name
        lines = path.read_text(encoding="utf-8").count("\n") if path.is_file() else 0
        out.append((name, lines, entry["review"]))
    return sorted(out, key=lambda r: -r[1])


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default="Fanfics", help="Папка (по умолчанию Fanfics)")
    ap.add_argument("--map", default=str(MAP_FILE), help="Карта границ")
    ap.add_argument("--apply", action="store_true", help="Записать изменения")
    args = ap.parse_args()

    directory = VAULT / args.folder
    mapping = json.loads(Path(args.map).read_text(encoding="utf-8"))

    report = [f"# Обёртка голых запросов: {args.folder}", "",
              f"Режим: {'запись' if args.apply else 'dry-run, ничего не меняется'}.", ""]
    done = prompts = lost_count = already = 0
    failures: list[tuple[str, str]] = []

    for name in sorted(mapping):
        path = directory / name
        if not path.is_file():
            failures.append((name, "нет такого файла"))
            continue
        text = path.read_text(encoding="utf-8")
        if not notes.has_tag_header(text):
            failures.append((name, "нет шапки — не понять, где начинается тело"))
            continue
        offset, body = body_offset(text)
        if runs_mod.uses_new_format(body):
            # Обёрнута прошлой партией: карта хранит всю историю разметки.
            already += 1
            continue
        try:
            spans = resolve(mapping[name], text)
        except MapError as e:
            failures.append((name, str(e)))
            continue
        new_body = wrap(body, spans)
        problem = check(body, new_body, spans)
        if problem:
            failures.append((name, problem))
            continue

        done += 1
        lost_here = sum(1 for a, b in spans if a == b)
        prompts += len(spans) - lost_here
        lost_count += lost_here
        report.append(f"## {name}")
        report.append("")
        report.extend(describe(body, spans, offset))
        report.append("")
        if args.apply:
            prefix = "\n".join(text.split("\n")[:offset])
            # newline="\n": заметки хранятся в LF (.gitattributes), а write_text
            # на Windows иначе молча пишет CRLF.
            path.write_text(prefix + "\n" + "\n".join(new_body) + "\n",
                            encoding="utf-8", newline="\n")

    summary = [f"заметок к записи: {done}", f"  голых запросов: {prompts}",
               f"  заглушек: {lost_count}", f"уже обёрнуты раньше: {already}",
               f"отказов: {len(failures)}"]
    report[4:4] = [*summary, ""]
    review = review_list(directory, mapping)
    summary.append(f"к разбору с усилием (по всей карте): {len(review)}")
    report[4:4] = [summary[-1]]
    if review:
        report.append("## К разбору с усилием")
        report.append("")
        report.append("Границы ответов здесь не видны или поставлены наугад — "
                      "пройти отдельно, чтобы заметка не осталась одним прогоном.")
        report.append("")
        report.extend(f"- {n} — {lines} строк: {why}" for n, lines, why in review)
        report.append("")
    if failures:
        report.append("## Отказы")
        report.append("")
        report.extend(f"- {n}: {why}" for n, why in failures)
    out = reports_dir(__file__) / REPORT_FILE
    out.write_text("\n".join(report) + "\n", encoding="utf-8")

    print("\n".join(summary))
    for n, why in failures:
        print(f"  ! {n}: {why}")
    print(f"отчёт: {out}")


if __name__ == "__main__":
    main()
