# -*- coding: utf-8 -*-
"""Переводит разметку диалога со служебных строк на свёрнутые callout.

Было — служебные строки посреди прозы:

    **Вы:**

    напиши длинную главу про…

    **Ассистент:**

    Текст главы…

Стало — запрос в свёрнутом callout, ответ идёт прозой без всякого маркера:

    > [!question]- Запрос 3
    > напиши длинную главу про…

    Текст главы…

Блок размышлений модели (в дампе он выглядит как второй `**Ассистент:**`
внутри одного прогона) уезжает в свой свёрнутый callout `Размышления`.

Границы прогонов берутся из `lib/runs.py` — того же модуля, которым читают
заметки выжимка описаний и поиск перезапусков. Строки промпта конвертер
берёт из файла как есть, без склейки: переносы внутри запроса значимы.

**Что конвертер не трогает** (и пишет в отчёт):

- заметки, где уже новый формат — повторный прогон безопасен;
- прогоны без `**Ассистент:**`: там нельзя отличить запрос от главы, и
  обёртка съела бы текст целиком. Таких мало, они разбираются руками.

Каждый файл после сборки перечитывается новым разбором: запрос и объём
ответа обязаны совпасть с тем, что было до правки. Не совпало — файл
не пишется вовсе.

По умолчанию ничего не меняет. Запись — с `--apply`.

  python Scripts/tools/convert_prompt_markup.py --folder Beta
  python Scripts/tools/convert_prompt_markup.py --folder Beta --apply
  python Scripts/tools/convert_prompt_markup.py --folder Fanfics --show 2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent.parent / "lib"
if str(_LIB) not in sys.path:
    sys.path.insert(0, str(_LIB))
import notes
import runs as runs_mod
from paths import vault_root
from runs import OLD_ANSWER_MARK, OLD_PROMPT_MARK, parse_runs

VAULT = vault_root(__file__)
CONTENT_FILE = "1. Content.md"


def trim(lines: list[str]) -> list[str]:
    out = list(lines)
    while out and not out[0].strip():
        out.pop(0)
    while out and not out[-1].strip():
        out.pop()
    return out


def convert_thinking_body(body: list[str]) -> tuple[list[str], list[str]]:
    """Тело дампа второго вида: запрос в callout, служебная строка убирается.

    Строка «Думал на протяжении 11s» — артефакт интерфейса, текста
    размышлений в ней нет, поэтому она просто исчезает. Там, где запроса
    не было вовсе (генерацию продолжили без текста), остаётся только проза.
    """
    out: list[str] = []
    notes_on: list[str] = []
    cursor = 0
    number = 0

    segments = runs_mod.thinking_segments(body)
    for n, seg in enumerate(segments):
        head = body[cursor:seg.prompt_start]
        while head and not head[-1].strip():
            head.pop()
        out.extend(head)
        cursor = seg.end

        # Ответ кончается там, где начинается **запрос** следующего сегмента,
        # а не на его служебной строке: между ними лежит сам запрос, и без
        # этой границы он попадал бы в текст дважды.
        stop = segments[n + 1].prompt_start if n + 1 < len(segments) else seg.end
        # Между запросом и служебной строкой обычно только пробелы, но у части
        # черновиков там уже начало ответа — его надо сохранить, а не потерять.
        middle = trim([l for l in body[seg.prompt_end:seg.mark]])
        answer = trim([l for l in body[seg.mark + 1:stop]])
        if middle:
            answer = middle + [""] + answer
        if seg.kind == "none":
            notes_on.append(f"строка {seg.mark}: запроса нет, генерацию продолжили "
                            f"без текста — убран только служебный маркер")
            if out and out[-1].strip():
                out.append("")
            out.extend(answer)
            out.append("")
            continue

        number += 1
        prompt = trim(body[seg.prompt_start:seg.prompt_end])
        if seg.kind != "spacer":
            how = {"short": "граница определена по длине блока",
                   "command": "граница определена по первому слову",
                   "leading": "взят из начала тела: ниже него уже идёт ответ"}
            notes_on.append(f"запрос {number}: {how[seg.kind]}")
        if out and out[-1].strip():
            out.append("")
        out.extend(runs_mod.render_callout(runs_mod.PROMPT_CALLOUT,
                                           f"{runs_mod.PROMPT_LABEL} {number}", prompt))
        out.append("")
        out.extend(answer)
        out.append("")

    out.extend(body[cursor:])
    while out and not out[-1].strip():
        out.pop()
    return out, notes_on


def convert_body(body: list[str]) -> tuple[list[str], list[str]]:
    """Новое тело и список причин, по которым часть прогонов осталась старой."""
    parsed = parse_runs(body)
    skipped: list[str] = []
    out: list[str] = []
    cursor = 0

    for n, run in enumerate(parsed, start=1):
        # Всё, что лежит до прогона (обычно преамбула заметки), переносим как есть.
        out.extend(body[cursor:run.start])
        cursor = run.end
        block = body[run.start:run.end]

        marks = [i for i, l in enumerate(block) if l.strip() == OLD_ANSWER_MARK]
        if not marks:
            skipped.append(f"прогон {n}: нет строки «{OLD_ANSWER_MARK}»")
            out.extend(block)
            continue

        prompt = trim(block[1:marks[0]])
        if len(marks) > 1:
            think = trim(block[marks[0] + 1:marks[1]])
            answer = trim(block[marks[1] + 1:])
        else:
            think, answer = [], trim(block[marks[0] + 1:])

        out.extend(runs_mod.render_callout(runs_mod.PROMPT_CALLOUT,
                                           f"{runs_mod.PROMPT_LABEL} {n}", prompt))
        out.append("")
        if think:
            out.extend(runs_mod.render_callout(runs_mod.THINK_CALLOUT,
                                               runs_mod.THINK_LABEL, think))
            out.append("")
        out.extend(answer)
        out.append("")

    out.extend(body[cursor:])
    while out and not out[-1].strip():
        out.pop()
    return out, skipped


def content_seq(lines: list[str], new_format: bool) -> list[str]:
    """Значимые строки тела: то, что обязано пережить конвертацию дословно.

    Отбрасывается только служебное — старые маркеры и заголовки callout.
    Кавычка `> `, которую конвертер добавил строкам запроса, снимается **лишь
    внутри callout**: в прозе ответа цитаты встречаются сами по себе (6419
    строк по хранилищу), и снимать `> ` у них — значит сравнивать разное
    и получать ложные расхождения.

    Порядок сохраняется: сверка идёт последовательностью, а не множеством,
    иначе перестановка абзацев прошла бы незамеченной.
    """
    out: list[str] = []
    in_callout = False
    for line in lines:
        s = line.strip()
        if not s:
            in_callout = False
            continue
        # Старые маркеры отбрасываются в обоих телах: прогон без ответа
        # конвертер не трогает, и они законно остаются в новом файле.
        if s in (OLD_PROMPT_MARK, OLD_ANSWER_MARK):
            continue
        # То же для служебной строки дампа второго вида: она исчезает
        # при конвертации, и сверять её не с чем.
        if runs_mod.THINKING_MARK_RE.match(s):
            continue
        if new_format:
            # Снимаются только свои callout — запрос и размышления. Чужой
            # (`> [!note] Примечания к главе`) — текст ответа: его сверяют
            # как есть, иначе заметка с ним не сходится по числу строк.
            m = runs_mod._CALLOUT_RE.match(s)
            if m and m.group(1).lower() in (runs_mod.PROMPT_CALLOUT,
                                            runs_mod.THINK_CALLOUT):
                in_callout = True
                continue
            if in_callout and s.startswith(">"):
                # Ровно один уровень: цитата, которая была в самом запросе,
                # должна остаться цитатой.
                s = s[1:].lstrip(" ")
                if not s:
                    continue
            else:
                in_callout = False
        out.append(s)
    return out


def verify(old_body: list[str], new_body: list[str]) -> str:
    """Пустая строка — сходится. Иначе текст расхождения.

    Сверяется не «примерно столько же строк», а дословное совпадение всего
    значимого текста по порядку: единственное, что конвертеру разрешено, —
    убрать два служебных маркера и приписать `> ` строкам запроса.
    """
    old = content_seq(old_body, new_format=False)
    new = content_seq(new_body, new_format=True)
    if old == new:
        return ""
    if len(old) != len(new):
        return f"строк текста было {len(old)}, стало {len(new)}"
    for n, (a, b) in enumerate(zip(old, new), start=1):
        if a != b:
            return f"строка {n} разошлась: {a[:40]!r} против {b[:40]!r}"
    return "неизвестное расхождение"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--folder", default="Beta", help="Папка (по умолчанию Beta)")
    ap.add_argument("--apply", action="store_true", help="Записать изменения")
    ap.add_argument("--show", type=int, default=0,
                    help="Показать начало нового тела у N заметок")
    args = ap.parse_args()

    directory = VAULT / args.folder
    if not directory.is_dir():
        sys.exit(f"Нет папки: {directory}")

    done = already = untouched = 0
    runs_converted = thinks = 0
    skips: list[tuple[str, str]] = []
    failures: list[tuple[str, str]] = []
    shown = 0

    for path in sorted(directory.glob("*.md")):
        if path.name == CONTENT_FILE:
            continue
        text = path.read_text(encoding="utf-8")
        body_text = notes.body_after_separator(text)
        body = body_text.split("\n")

        if runs_mod.uses_new_format(body):
            already += 1
            continue

        if runs_mod.uses_thinking_format(body):
            new_body, skipped = convert_thinking_body(body)
        elif any(l.strip() == OLD_PROMPT_MARK for l in body):
            new_body, skipped = convert_body(body)
        else:
            untouched += 1
            continue

        problem = verify(body, new_body)
        if not problem:
            # Шапка определяется по первым строкам, а конвертация их сдвигает:
            # у заметки без шапки «---» из тела может подняться в её пределы,
            # и тогда скрипты начнут принимать начало текста за шапку.
            prefix = text[:len(text) - len(body_text)] if body_text else ""
            if notes.has_tag_header(prefix + "\n".join(new_body)) \
                    != notes.has_tag_header(text):
                problem = "изменилось, считается ли начало файла шапкой"
        if problem:
            failures.append((path.name, problem))
            continue
        converted = sum(1 for l in new_body
                        if l.startswith(f"> [!{runs_mod.PROMPT_CALLOUT}]"))
        if not converted:
            # Разметка есть, но конвертировать нечего: единственный прогон
            # остался старым (см. список пропущенных ниже). Файл не трогаем —
            # иначе запись отличалась бы от исходника пустой строкой в хвосте.
            skips.extend((path.name, why) for why in skipped)
            untouched += 1
            continue

        skips.extend((path.name, why) for why in skipped)
        done += 1
        runs_converted += converted
        thinks += sum(1 for l in new_body if l.startswith(f"> [!{runs_mod.THINK_CALLOUT}]"))

        if shown < args.show:
            shown += 1
            print(f"\n--- {path.name}: первые 18 строк нового тела")
            for l in new_body[:18]:
                print(f"    {l[:110]}")
            print("---")

        if args.apply:
            prefix = text[:len(text) - len(body_text)] if body_text else text
            path.write_text(prefix + "\n".join(new_body) + "\n",
                            encoding="utf-8", newline="\n")

    print(f"\n# Конвертация разметки: {args.folder}")
    print(f"  режим: {'ЗАПИСЬ' if args.apply else 'dry-run, ничего не меняется'}")
    print(f"  заметок к конвертации: {done}")
    print(f"    в них запросов: {runs_converted}, из них с размышлениями: {thinks}")
    print(f"  уже в новом формате: {already}")
    print(f"  без разметки диалога (не трогаем): {untouched}")

    print(f"\n## Прогоны, оставленные в старом виде: {len(skips)}")
    for name, why in skips:
        print(f"    {name} | {why}")

    print(f"\n## Не записаны, самопроверка не сошлась: {len(failures)}")
    for name, why in failures:
        print(f"    {name} | {why}")


if __name__ == "__main__":
    main()
